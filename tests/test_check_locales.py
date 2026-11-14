import json
from pathlib import Path
import tempfile
import unittest

from tools.check_locales import icu_arguments, parameters, validate, validate_web


class CatalogValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for language in ('hu', 'en'):
            (self.root / language).mkdir()

    def write(self, language, data, name='common.json'):
        (self.root / language / name).write_text(json.dumps(data), encoding='utf-8')

    def test_plural_forms_and_escaped_braces(self):
        self.write('hu', {'coins': '{count} érme {{literal}}'})
        self.write('en', {'coins': {'one': '{count} coin {{literal}}', 'other': '{count} coins'}})
        self.assertEqual(validate(self.root), ([], 2))
        self.assertEqual(parameters('{n|coin|coins} {{ignore}} {amount:.2f}'), {'n', 'amount'})

    def test_missing_parameter_is_rejected_in_each_plural_form(self):
        self.write('hu', {'coins': '{count} érme'})
        self.write('en', {'coins': {'one': '{count} coin', 'other': 'coins'}})
        self.assertTrue(any('placeholder mismatch' in x for x in validate(self.root)[0]))

    def test_missing_keys_and_empty_translations_are_rejected(self):
        self.write('hu', {'hello': 'Hello', 'missing': 'Missing'})
        self.write('en', {'hello': ''})
        errors, _ = validate(self.root)
        self.assertTrue(any('missing key' in x for x in errors))
        self.assertTrue(any('empty translation' in x for x in errors))

    def test_duplicate_json_keys_are_not_silently_overwritten(self):
        self.write('hu', {'hello': 'Hello'})
        (self.root / 'en' / 'common.json').write_text('{"hello":"a","hello":"b"}', encoding='utf-8')
        self.assertTrue(any('duplicate JSON key' in x for x in validate(self.root)[0]))

    def test_nested_command_descriptions_must_match(self):
        self.write('hu', {'commands': {'ping': {'name': 'ping', 'description': 'Ping'}}}, 'commands.json')
        self.write('en', {'commands': {'ping': {'name': 'ping'}}}, 'commands.json')
        self.assertTrue(any('missing key' in x for x in validate(self.root)[0]))

    def test_missing_reference_catalog_fails(self):
        self.assertTrue(validate(self.root)[0])


class WebCatalogValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for language in ('hu', 'en'):
            (self.root / language).mkdir()

    def write(self, language, data, name='common.json'):
        (self.root / language / name).write_text(json.dumps(data), encoding='utf-8')

    def errors(self):
        return validate_web(self.root)[0]

    def test_icu_plural_and_tags_pass(self):
        self.write('hu', {'list': {'count': '{count, plural, one {# tag} other {# tag}} a <b>{name}</b> szerveren'}})
        self.write('en', {'list': {'count': '{count, plural, one {# member} other {# members}} on <b>{name}</b>'}})
        self.assertEqual(self.errors(), [])

    def test_quoted_icu_text_is_not_a_placeholder(self):
        self.assertEqual(icu_arguments("Use '{szam}' in the template, {n} left"), {'n'})

    def test_placeholder_tag_and_brace_problems_are_reported(self):
        self.write('hu', {'a': '{name} <b>x</b>', 'b': '{n, plural, other {#}}'})
        self.write('en', {'a': '{nev} x', 'b': '{n, plural, other {#}'})
        errors = self.errors()
        for problem in ('placeholder mismatch', 'tag mismatch', 'unbalanced'):
            self.assertTrue(any(problem in e for e in errors), problem)

    def test_emoji_missing_keys_and_files_are_reported(self):
        self.write('hu', {'a': 'Szia', 'b': 'Kész'})
        self.write('en', {'a': 'Hi 🍊'})
        self.write('hu', {'x': 'y'}, 'nav.json')
        errors = self.errors()
        self.assertTrue(any('emoji' in e for e in errors))
        self.assertTrue(any('missing key b' in e for e in errors))
        self.assertTrue(any('nav.json: missing file' in e for e in errors))

    def test_dictionary_command_lists_are_optional(self):
        self.write('hu', {'capabilities': {'mod.ban': {'label': 'Kitiltás', 'commands': '/ban'}}}, '_dictionary.json')
        self.write('en', {'capabilities': {'mod.ban': {'label': 'Bans'}}}, '_dictionary.json')
        self.assertEqual(self.errors(), [])


class RepositoryTests(unittest.TestCase):
    def test_published_catalogs_are_valid(self):
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(validate(root / 'bot')[0], [])
        self.assertEqual(validate_web(root / 'web')[0], [])


if __name__ == '__main__':
    unittest.main()
