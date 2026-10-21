# OrangenBOT – Fordítások (locales)

Ez a repó az **OrangenBOT** nyelvi fájljait (`locales`) tartalmazza.
Ha szeretnétek, **csináljatok fordítást** – bárki segíthet, hogy a bot minél több nyelven elérhető legyen! 🍊

## Felépítés

```
locales/
├── hu/   # magyar (eredeti)
├── en/   # angol
└── de/   # német
```

Minden nyelv mappájában ugyanazok a `.json` fájlok vannak (pl. `common.json`, `music.json`, `tickets.json` …),
modulonként szétszedve. Egy fájl egyszerű kulcs–érték párokból áll:

```json
{
  "yes": "Igen",
  "no": "Nem"
}
```

## Hogyan fordíts?

1. **Forkold** a repót.
2. Új nyelvnél másold le az `en` (vagy `hu`) mappát, és nevezd el a nyelv kódjára
   (pl. `locales/fr`, `locales/es`, `locales/pl`).
   Meglévő nyelv javításánál csak szerkeszd a megfelelő fájlt.
3. **Csak az értékeket fordítsd le**, a kulcsokat (a `:` előtti részt) ne!
4. Nyiss egy **Pull Requestet** – átnézzük és bekerül a botba.

## Szabályok, amikre figyelj

- A kulcsokat **ne** változtasd meg, és ne törölj ki egyet sem.
- A változókat, pl. `{user}`, `{count}`, `{0}` hagyd **pontosan** úgy, ahogy vannak (a mondatban áthelyezheted őket).
- A Discord formázást (`**félkövér**`, `` `kód` ``, `\n`, emojik, `<@...>`) tartsd meg.
- A fájl maradjon **érvényes JSON** (idézőjelek, vesszők!) és **UTF-8** kódolású.
- Ha valamit nem tudsz lefordítani, hagyd angolul – jobb, mint egy rossz fordítás.

Köszönjük mindenkinek, aki segít! ❤️
