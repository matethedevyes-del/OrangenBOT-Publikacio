"""Validate the bot (`bot/`) and website (`web/`) translations without third-party packages.

    python3 tools/check_locales.py            # both
    python3 tools/check_locales.py bot        # only one of them

Every language is compared to Hungarian (`hu`), the source language: same files, same keys, same
placeholders; no empty or duplicated entries. Bot texts use Python placeholders (`{name}`, `{n|coin|coins}`,
one/other plural objects); website texts use ICU MessageFormat (`{count, plural, one {…} other {…}}`,
`<b>…</b>` tags) and must not contain emoji.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

PLACEHOLDER = re.compile(r"\{\{|\}\}|\{([A-Za-z_][A-Za-z0-9_]*)(?:\|([^{}|]*)\|([^{}]*)|:([^{}]*))?\}")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def forms(value):
    if isinstance(value, str):
        return [value]
    if (isinstance(value, dict) and value and "other" in value
            and set(value) <= {"one", "other"} and all(isinstance(x, str) for x in value.values())):
        return list(value.values())
    raise ValueError("expected a string or one/other plural object with an other form")


def parameters(text):
    return {m.group(1) for m in PLACEHOLDER.finditer(text) if m.group(1)}


def command_leaves(data, prefix=()):
    if isinstance(data, str):
        return {prefix: data}
    if not isinstance(data, dict) or not data:
        raise ValueError("command entries must contain strings")
    result = {}
    for key, value in data.items():
        result.update(command_leaves(value, (*prefix, key)))
    return result


def validate(root: Path) -> tuple[list[str], int]:
    errors, catalogs = [], {}
    languages = sorted(p for p in root.iterdir() if p.is_dir()) if root.is_dir() else []
    if not languages or not (root / "hu").is_dir():
        return ["Missing bot/hu reference catalog"], 0
    reference = {p.name for p in (root / "hu").glob("*.json")}
    if not reference:
        return ["Empty Hungarian reference catalog"], 0
    count = 0
    for folder in languages:
        files = {p.name for p in folder.glob("*.json")}
        for name in sorted(reference - files):
            errors.append(f"{folder.name}/{name}: missing file")
        for name in sorted(files - reference):
            errors.append(f"{folder.name}/{name}: unexpected file")
        for name in sorted(files):
            path = folder / name
            count += 1
            try:
                data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
                if not isinstance(data, dict):
                    raise ValueError("expected a JSON object")
                if name == "commands.json":
                    data = command_leaves(data)
                for value in data.values():
                    forms(value)
                catalogs[folder.name, name] = data
            except (OSError, ValueError) as exc:
                errors.append(f"{folder.name}/{name}: {exc}")
    for (language, name), data in catalogs.items():
        base = catalogs.get(("hu", name))
        if language == "hu" or base is None:
            continue
        for key in sorted(base.keys() - data.keys()):
            errors.append(f"{language}/{name}: missing key {key}")
        for key in sorted(data.keys() - base.keys()):
            errors.append(f"{language}/{name}: unexpected key {key}")
        for key in base.keys() & data.keys():
            expected = set().union(*(parameters(f) for f in forms(base[key])))
            for value in forms(data[key]):
                if parameters(value) != expected:
                    errors.append(f"{language}/{name}:{key}: placeholder mismatch")
                if not value.strip() and any(f.strip() for f in forms(base[key])):
                    errors.append(f"{language}/{name}:{key}: empty translation")
    return errors, count


validate_bot = validate

# --------------------------------------------------------------------------- website (ICU MessageFormat)

DICTIONARY = "_dictionary.json"
ICU_QUOTED = re.compile(r"'[^']*'")
ICU_ARGUMENT = re.compile(r"\{\s*(\w+)\s*[,}]")
ICU_TAG = re.compile(r"</?([A-Za-z][\w-]*)\s*/?>")
# The same pictographs the website's own test rejects (©, ® and ™ are typography, not emoji).
EMOJI = re.compile(
    "[\u203c\u2049\u2139\u2194-\u2199\u21a9\u21aa\u231a\u231b\u2328\u23cf\u23e9-\u23f3\u23f8-\u23fa\u24c2"
    "\u25aa\u25ab\u25b6\u25c0\u25fb-\u25fe\u2600-\u27bf\u2934\u2935\u2b05-\u2b07\u2b1b\u2b1c\u2b50\u2b55"
    "\u3030\u303d\u3297\u3299\U0001f000-\U0001faff\ufe0f]"
)


def icu_arguments(text: str) -> set[str]:
    return set(ICU_ARGUMENT.findall(ICU_QUOTED.sub("", text)))


def icu_tags(text: str) -> list[str]:
    return sorted(ICU_TAG.findall(ICU_QUOTED.sub("", text)))


def icu_balanced(text: str) -> bool:
    depth = 0
    for ch in ICU_QUOTED.sub("", text):
        depth += {"{": 1, "}": -1}.get(ch, 0)
        if depth < 0:
            return False
    return depth == 0


def tree_leaves(data, prefix=""):
    if isinstance(data, dict):
        if not data:
            raise ValueError(f"{prefix or 'root'}: empty object")
        result = {}
        for key, value in data.items():
            result.update(tree_leaves(value, f"{prefix}.{key}" if prefix else key))
        return result
    if not isinstance(data, str):
        raise ValueError(f"{prefix}: expected text")
    return {prefix: data}


def validate_web(root: Path) -> tuple[list[str], int]:
    errors, catalogs = [], {}
    if not (root / "hu").is_dir():
        return ["Missing web/hu reference catalog"], 0
    reference = {p.name for p in (root / "hu").glob("*.json")}
    count = 0
    for folder in sorted(p for p in root.iterdir() if p.is_dir()):
        files = {p.name for p in folder.glob("*.json")}
        for name in sorted(reference - files):
            errors.append(f"web/{folder.name}/{name}: missing file")
        for name in sorted(files - reference):
            errors.append(f"web/{folder.name}/{name}: unexpected file")
        for name in sorted(files):
            count += 1
            try:
                data = json.loads((folder / name).read_text(encoding="utf-8"), object_pairs_hook=unique_object)
                catalogs[folder.name, name] = tree_leaves(data)
            except (OSError, ValueError) as exc:
                errors.append(f"web/{folder.name}/{name}: {exc}")
    for (language, name), data in catalogs.items():
        where = f"web/{language}/{name}"
        for key, value in data.items():
            if not value.strip():
                errors.append(f"{where}:{key}: empty translation")
            if EMOJI.search(value):
                errors.append(f"{where}:{key}: emoji are not allowed on the website")
            if not icu_balanced(value):
                errors.append(f"{where}:{key}: unbalanced {{ }}")
        base = catalogs.get(("hu", name))
        if language == "hu" or base is None:
            continue
        for key in sorted(base.keys() - data.keys()):
            # the dictionary's command lists are optional: without a translation the Hungarian one is shown
            if not (name == DICTIONARY and key.endswith(".commands")):
                errors.append(f"{where}: missing key {key}")
        for key in sorted(data.keys() - base.keys()):
            errors.append(f"{where}: unexpected key {key}")
        for key in sorted(base.keys() & data.keys()):
            if icu_arguments(data[key]) != icu_arguments(base[key]):
                errors.append(f"{where}:{key}: placeholder mismatch")
            if icu_tags(data[key]) != icu_tags(base[key]):
                errors.append(f"{where}:{key}: tag mismatch")
    return errors, count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("part", nargs="?", choices=("all", "bot", "web"), default="all")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors, summary = [], []
    if args.part in ("all", "bot"):
        found, count = validate_bot(args.root / "bot")
        errors += [f"bot/{e}" if not e.startswith("Missing") and not e.startswith("Empty") else e for e in found]
        summary.append(f"{count} bot files")
    if args.part in ("all", "web"):
        found, count = validate_web(args.root / "web")
        errors += found
        summary.append(f"{count} website files")
    if errors:
        print("\n".join(errors))
        print(f"\n{len(errors)} problem(s).")
        return 1
    print(f"Validated {' and '.join(summary)}: keys, placeholders, plurals, tags and duplicate keys OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
