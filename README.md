# OrangenBOT – Fordítások · Translations

Ez a repó az **OrangenBOT** Discord-bot és a hozzá tartozó **weboldal / vezérlőpult** ([orangenbot.com](https://orangenbot.com)) összes szövegét tartalmazza, nyelvenként.
Bárki segíthet: javíts egy fordítást, vagy hozz egy új nyelvet! 🍊

*This repository holds every text of the OrangenBOT Discord bot and its website / dashboard, per language. Anyone can help: fix a translation or add a new language. English summary at the bottom.*

| | Mappa | Fájlok / nyelv | Szövegek / nyelv | Nyelvek |
|---|---|---|---|---|
| 🤖 Bot (Discord-üzenetek, parancsok) | [`bot/`](bot) | 83 | ~9 900 | 🇭🇺 hu · 🇬🇧 en · 🇩🇪 de |
| 🌐 Weboldal és vezérlőpult | [`web/`](web) | 54 | ~5 100 | 🇭🇺 hu · 🇬🇧 en · 🇩🇪 de |

Forrás: bot **8.5.2**, a weboldal mai `main` állapota. A **magyar (`hu`) az eredeti**: minden más nyelv ehhez igazodik.

## Felépítés

```
bot/
├── hu/                 # magyar (eredeti)
│   ├── common.json     # modulonként egy fájl: eco.json, music.json, tickets.json, …
│   └── commands.json   # a perjeles parancsok nevei, leírásai, opciói
├── en/
└── de/
web/
├── hu/                 # magyar (eredeti)
│   ├── landing.json    # a weboldal egy-egy része: főoldal, vezérlőpult, beállítások, …
│   ├── commands.json   # a nyilvános „Parancsok” lap
│   └── _dictionary.json  # a vezérlőpult szótára: minden beállítás, modul, jog neve és leírása
├── en/
└── de/
tools/                  # ellenőrző és szinkronizáló eszközök
tests/
```

Minden nyelv mappájában **ugyanazok a fájlok** vannak, ugyanazokkal a kulcsokkal.

## Hogyan fordíts?

1. **Forkold** a repót (vagy kis javításnál szerkeszd közvetlenül a GitHubon: ✏️ gomb a fájlon).
2. Keresd meg a szöveget: a repó keresője a magyar mondatra is talál, és megmutatja a fájlt és a kulcsot.
3. **Csak az értékeket fordítsd**, a kulcsokat (a `:` előtti részt) soha.
4. Futtasd az ellenőrzőt (lásd lent), majd nyiss egy **Pull Requestet** – átnézzük, és bekerül a botba / a weboldalra.

**Új nyelv:** másold le az `en` mappát `bot/` és `web/` alatt is a nyelv kódjára (pl. `bot/fr`, `web/fr`), és fordítsd le.
A bot új nyelvét a következő kiadásban bekapcsoljuk; a weboldalé egy kis kódmódosítást is igényel, azt mi intézzük.

## Szabályok

### Közös
- A kulcsokat **ne** változtasd meg, ne törölj és ne adj hozzá újat.
- A fájl maradjon **érvényes JSON** (idézőjelek, vesszők!), **UTF-8** kódolással.
- Ha valamit nem tudsz jól lefordítani, hagyd angolul – jobb, mint egy rossz fordítás.

### 🤖 Bot (`bot/`)
- A változókat, pl. `{name}`, `{mention}`, `{money}` hagyd **pontosan** úgy (a mondatban áthelyezheted).
- Többes szám: `{n|érme|érme}` (egyes|többes), vagy `{"one": "…", "other": "…"}` objektum.
- A Discord-formázás maradjon: `**félkövér**`, `` `kód` ``, `\n`, `<@…>`, emojik.
- `commands.json`: a parancsnevek **kisbetűsek, szóköz nélküliek** (max. 32 karakter), a leírások max. 100 karakter (Discord-szabály).

### 🌐 Weboldal (`web/`)
- ICU-formátum: a változók `{name}`, a többes szám `{count, plural, one {# tag} other {# tagok}}` – a `plural`, `one`, `other` és a `#` marad, csak a szöveget fordítsd.
- A címkék (`<b>…</b>`, `<link>…</link>`, `<code>…</code>`) maradnak, csak a közéjük írt szöveget fordítsd.
- `'{szam}'` (aposztrófok között) szó szerinti szöveg – maradjon így.
- **Emoji nem kerülhet** a weboldal szövegeibe (a felület saját ikonokat használ).
- `_dictionary.json`: a `commands` mezők (parancslisták) elhagyhatók – ilyenkor a magyar parancsnevek látszanak.

## Automatikus ellenőrzés

```bash
python3 tools/check_locales.py        # bot + web (Python 3.12+, külső csomag nélkül)
python3 tools/check_locales.py web    # csak a weboldal
python3 -m unittest discover -s tests # az ellenőrző saját tesztjei
```

Minden nyelvet a magyarhoz hasonlít: hiányzó / fölösleges fájlok és kulcsok, helyőrzők, többes számok, ICU-címkék és zárójelek, üres fordítások, duplikált JSON-kulcsok, emoji a weboldalon.
A GitHub Actions minden pushnál és pull requestnél lefuttatja.

## Karbantartóknak: szinkronizálás

A szövegek forrása a bot (`dcbot2.0`) és a weboldal (`orangenweboldal`) kódja. A `tools/sync.py` mindkét irányba visz:

```bash
python3 tools/sync.py pull --bot ../dcbot2.0 --web ../orangenweboldal   # a legújabb szövegek ide
python3 tools/sync.py push --bot ../dcbot2.0 --web ../orangenweboldal   # az elfogadott fordítások vissza
```

A `push` a magyart sosem írja vissza (az a kódban él), és a kimenet bájtra azonos a forrás formátumával – egy `pull` utáni `push` nem változtat semmin.
Utána a bot és a weboldal saját tesztjei (`pytest`, `npm test`) is lefutnak, mielőtt a fordítás élesbe kerül.

---

## English summary

- `bot/<lang>/*.json` – the Discord bot's texts (one file per module, `commands.json` holds slash-command names and descriptions). Python placeholders: `{name}`, `{n|singular|plural}`, `{"one": …, "other": …}`.
- `web/<lang>/*.json` – the website and dashboard (one file per section; `_dictionary.json` is the dashboard's dictionary of every setting, module and permission). ICU MessageFormat: `{name}`, `{count, plural, one {…} other {…}}`, `<b>…</b>` tags; no emoji.
- Hungarian (`hu`) is the source. Translate only the values, never the keys; keep every placeholder and tag.
- Run `python3 tools/check_locales.py` before opening a pull request. New language: copy `en` under both `bot/` and `web/`.

Köszönjük mindenkinek, aki segít! ❤️ · Közreműködők / Contributors: [Claude és OpenAI Codex](CONTRIBUTORS.md).
