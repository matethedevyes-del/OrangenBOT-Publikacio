import json
from pathlib import Path
import tempfile
import unittest

from tools.check_locales import parameters, validate


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


if __name__ == '__main__':
    unittest.main()
