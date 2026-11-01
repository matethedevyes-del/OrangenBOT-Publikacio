"""Validate translation files without installing the bot or third-party packages."""
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
        return ["Missing locales/hu reference catalog"], 0
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
                if not isinstance(data, dict) or not data:
                    raise ValueError("expected a nonempty JSON object")
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parents[1] / "locales")
    args = parser.parse_args()
    errors, count = validate(args.root)
    if errors:
        print("\n".join(errors))
        return 1
    print(f"Validated {count} JSON files: keys, placeholders, plurals and duplicate keys OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
