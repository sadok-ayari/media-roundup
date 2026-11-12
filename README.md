# media-roundup

A media monitoring digest that collects, filters, de-duplicates and groups coverage into a briefing you can send. One Python file, no dependencies.

It does the mechanical part — what came in, what is new, which story repeats across outlets, which topic it belongs to. It leaves the judgement to you: **the script does not summarise.** Deciding what an item means is the job of whoever signs the briefing, and pretending otherwise is how media reports become fiction.

```bash
python3 roundup.py --config examples/watchlist.json --out roundup.md
```

```
65 items -> roundup.md
```

## What it does

- **Collects** RSS 2.0 and Atom feeds.
- **Filters** to a time window (default 24 hours), so a stale item cannot survive a fresh brief.
- **De-duplicates** across outlets, keeping the earliest occurrence of the same story.
- **Groups** items under topics from a keyword map you control.
- **Reports coverage gaps** when a feed fails, instead of quietly returning a shorter brief.
- **Writes markdown** with outlet, headline, timestamp and link on every line.

## Configure it

`examples/watchlist.json`:

```json
{
  "title": "MEDIA ROUNDUP",
  "window_hours": 24,
  "classification": "",
  "feeds": [
    {"outlet": "Wire A", "url": "https://feeds.bbci.co.uk/news/world/rss.xml"},
    {"outlet": "Wire B", "url": "https://www.theguardian.com/world/rss"}
  ],
  "topics": [
    {"name": "Security", "keywords": ["conflict", "strike", "security"]},
    {"name": "Economy", "keywords": ["economy", "trade", "budget"]}
  ]
}
```

Anything that matches no topic lands in `Other`, which is where you look first: it is either a new topic or noise.

## Options

| Flag | Purpose |
|---|---|
| `--config` | watchlist file |
| `--out` | markdown output path, `-` for stdout |
| `--hours` | override the window |
| `--now` | treat a given ISO timestamp as now, for reproducible runs and tests |
| `--cache` | read saved `.xml` files instead of the network, for offline runs |

## Output shape

```markdown
# MEDIA ROUNDUP

Thursday, 12 November 2026

## Security

- **Wire A — Israeli strike on Nasser Hospital kills at least six** (12 Nov 03:32 UTC)
  https://www.bbc.co.uk/news/articles/...

## Coverage gaps

- Wire B: feed unreachable this run
```

## Tests

```bash
python3 -m unittest discover -s tests -v
```

Twelve tests, no network: RSS and Atom parsing, broken XML, missing dates, the freshness window, cross-outlet de-duplication, topic assignment, empty runs, failed feeds, and a full CLI run against cached fixtures.

## Limits, stated plainly

- **Feeds only.** No paywalled pages, no social platforms, no PDFs. If you need those, fetch them yourself and add the text.
- **Keyword grouping is crude on purpose.** It is auditable in a way a model's judgement is not.
- **No summaries, no scores, no sentiment.** Those are editorial acts; they belong to a person with a name on the brief.
- **Arabic and English items coexist** but no translation is attempted. Titles stay in the original language.

## Licence

MIT. Written by Sadok Ayari.
