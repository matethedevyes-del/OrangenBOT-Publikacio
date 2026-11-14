"""Synchronise this repository with the bot and website repositories (maintainers only).

    python3 tools/sync.py pull --bot ../dcbot2.0 --web ../orangenweboldal   # bot + web -> this repo
    python3 tools/sync.py push --bot ../dcbot2.0 --web ../orangenweboldal   # this repo -> bot + web

`pull` copies the bot's `locales/<lang>/*.json` to `bot/<lang>/` and splits the website's
`src/messages/<lang>.json` into one file per namespace under `web/<lang>/`. The website's dashboard
dictionary (the labels of every bot setting, module and permission) goes to `web/<lang>/_dictionary.json`:
English and German come from `src/messages/meta.<lang>.json`, the Hungarian reference is built from
`src/lib/bot-meta.json` (the bot's own Hungarian texts).

`push` writes accepted translations back. Hungarian is never written back: it is the source language and
lives in the code. `--bot` or `--web` may be given alone. No third-party packages are needed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
DICTIONARY = "_dictionary.json"
SOURCE = "hu"

# The same pictographs the website's own test rejects (©, ® and ™ are typography, not emoji).
EMOJI = re.compile(
    "[‼⁉ℹ↔-↙↩↪⌚⌛⌨⏏⏩-⏳⏸-⏺Ⓜ"
    "▪▫▶◀◻-◾☀-➿⤴⤵⬅-⬇⬛⬜⭐⭕"
    "〰〽㊗㊙\U0001f000-\U0001faff️‍]"
)


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def plain(text: str) -> str:
    """A label without its decorative emoji (the dictionary layers never contain any)."""
    return EMOJI.sub("", text or "").strip()


def hungarian_dictionary(meta: dict) -> dict:
    """The Hungarian reference in the same shape as the website's meta.<lang>.json overlays."""

    def optional(target: dict, key: str, value) -> None:
        if value:
            target[key] = plain(value)

    topics = {}
    for t in meta["topics"]:
        entry = {"title": plain(t["title"]), "summary": plain(t["summary"])}
        optional(entry, "commands", t.get("commands"))
        topics[t["key"]] = entry
    settings, units = {}, {}
    for s in meta["settings"]:
        entry = {"label": plain(s["label"]), "description": plain(s["description"])}
        optional(entry, "why", s.get("why"))
        optional(entry, "zero", s.get("zero"))
        special = s.get("special") or {}
        opts = {o["value"]: plain(o["label"]) for o in [*(special.get("options") or []), *(special.get("extra") or [])]}
        if opts:
            entry["options"] = opts
        if s.get("unit"):
            units[s["unit"]] = s["unit"]
        settings[s["key"]] = entry
    modules = {}
    for m in meta["modules"]:
        entry = {"title": plain(m["title"]), "summary": plain(m["summary"])}
        optional(entry, "hint", m.get("hint"))
        optional(entry, "offEffect", m.get("offEffect"))
        modules[m["key"]] = entry
    perms = meta["permissions"]
    capabilities = {}
    for c in perms["capabilities"]:
        entry = {"label": plain(c["label"]), "description": plain(c["description"])}
        optional(entry, "commands", c.get("commands"))
        capabilities[c["key"]] = entry
    return {
        "settings": settings,
        "topics": topics,
        "moduleGroups": {g["key"]: plain(g["title"]) for g in meta["moduleGroups"]},
        "modules": modules,
        "shop": {
            "kinds": {k: plain(v) for k, v in meta["shop"]["kinds"].items()},
            "items": {b["key"]: plain(b["name"]) for b in meta["shop"]["builtin"]},
        },
        "levels": {
            str(lv["value"]): {"label": plain(lv["label"]), "requirement": plain(lv["requirement"]),
                               "description": plain(lv["description"])}
            for lv in perms["levels"]
        },
        "capabilityGroups": {g["key"]: plain(g["title"]) for g in perms["groups"]},
        "capabilities": capabilities,
        "units": units,
    }


def languages(folder: Path) -> list[str]:
    return sorted(p.name for p in folder.iterdir() if p.is_dir()) if folder.is_dir() else []


def pull_bot(bot: Path) -> None:
    source = bot / "locales"
    if not (source / SOURCE).is_dir():
        sys.exit(f"{source}/{SOURCE} not found — is --bot the dcbot2.0 checkout?")
    target = ROOT / "bot"
    for lang in languages(source):
        shutil.rmtree(target / lang, ignore_errors=True)
        (target / lang).mkdir(parents=True)
        for f in sorted((source / lang).glob("*.json")):
            reference = source / SOURCE / f.name
            if reference.is_file() and not read(reference):
                continue   # a module whose texts were all removed: nothing to translate
            shutil.copyfile(f, target / lang / f.name)
    print(f"bot: {len(list(target.glob('*/*.json')))} files from {source}")


def pull_web(web: Path) -> None:
    messages = web / "src" / "messages"
    if not (messages / f"{SOURCE}.json").is_file():
        sys.exit(f"{messages}/{SOURCE}.json not found — is --web the orangenweboldal checkout?")
    target = ROOT / "web"
    shutil.rmtree(target, ignore_errors=True)
    for path in sorted(messages.glob("??.json")):
        lang = path.stem
        for namespace, tree in read(path).items():
            write(target / lang / f"{namespace}.json", tree)
        layer = messages / f"meta.{lang}.json"
        if lang == SOURCE:
            write(target / lang / DICTIONARY, hungarian_dictionary(read(web / "src" / "lib" / "bot-meta.json")))
        elif layer.is_file():
            write(target / lang / DICTIONARY, read(layer))
    print(f"web: {len(list(target.glob('*/*.json')))} files from {messages}")


def push_bot(bot: Path) -> None:
    target = bot / "locales"
    for lang in languages(ROOT / "bot"):
        if lang == SOURCE:
            continue
        (target / lang).mkdir(parents=True, exist_ok=True)
        for f in sorted((ROOT / "bot" / lang).glob("*.json")):
            shutil.copyfile(f, target / lang / f.name)
    print(f"bot: translations written to {target}")


def push_web(web: Path) -> None:
    messages = web / "src" / "messages"
    order = list(read(messages / f"{SOURCE}.json"))
    for lang in languages(ROOT / "web"):
        if lang == SOURCE:
            continue
        folder = ROOT / "web" / lang
        names = sorted(p.stem for p in folder.glob("*.json") if p.name != DICTIONARY)
        names.sort(key=lambda n: order.index(n) if n in order else len(order))
        write(messages / f"{lang}.json", {n: read(folder / f"{n}.json") for n in names})
        if (folder / DICTIONARY).is_file():
            write(messages / f"meta.{lang}.json", read(folder / DICTIONARY))
    print(f"web: translations written to {messages} (run its tests: npm test)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("direction", choices=("pull", "push"))
    parser.add_argument("--bot", type=Path, help="dcbot2.0 checkout")
    parser.add_argument("--web", type=Path, help="orangenweboldal checkout")
    args = parser.parse_args()
    if not args.bot and not args.web:
        parser.error("give --bot and/or --web")
    if args.bot:
        (pull_bot if args.direction == "pull" else push_bot)(args.bot.resolve())
    if args.web:
        (pull_web if args.direction == "pull" else push_web)(args.web.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
