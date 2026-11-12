"""Offline tests: no network, fixed clock, fixtures built in-code."""
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import roundup  # noqa: E402

NOW = datetime(2026, 11, 12, 9, 0, tzinfo=timezone.utc)

RSS = """<?xml version="1.0"?><rss version="2.0"><channel>
<item><title>Ministers sign water accord</title><link>https://a.example/1</link>
<pubDate>Wed, 12 Nov 2026 06:00:00 +0000</pubDate><description>Water deal signed.</description></item>
<item><title>Old story from last week</title><link>https://a.example/2</link>
<pubDate>Wed, 05 Nov 2026 06:00:00 +0000</pubDate></item>
</channel></rss>"""

ATOM = """<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom">
<entry><title>Ministers sign water accord</title>
<link rel="alternate" href="https://b.example/9"/>
<published>2026-11-12T06:30:00Z</published><summary>Same story, other paper.</summary></entry>
<entry><title>Budget debate opens</title>
<link rel="alternate" href="https://b.example/10"/>
<published>2026-11-12T07:15:00Z</published><summary>Parliament opens the budget debate.</summary></entry>
</feed>"""

CONFIG = {
    "title": "MEDIA ROUNDUP",
    "window_hours": 24,
    "feeds": [{"outlet": "Alpha", "url": "https://a.example/rss"},
              {"outlet": "Beta", "url": "https://b.example/atom"}],
    "topics": [{"name": "Water", "keywords": ["water"]},
               {"name": "Politics", "keywords": ["budget", "parliament"]}],
}


class TestParsing(unittest.TestCase):
    def test_rss_items(self):
        items = roundup.parse_feed(RSS.encode(), "Alpha")
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].outlet, "Alpha")
        self.assertEqual(items[0].link, "https://a.example/1")

    def test_atom_items(self):
        items = roundup.parse_feed(ATOM.encode(), "Beta")
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].link, "https://b.example/9")

    def test_broken_xml_is_empty_not_fatal(self):
        self.assertEqual(roundup.parse_feed(b"<rss>truncated", "Alpha"), [])

    def test_missing_date_is_dropped(self):
        xml = b"<rss><channel><item><title>No date</title></item></channel></rss>"
        self.assertEqual(roundup.parse_feed(xml, "Alpha"), [])


class TestWindowAndDedupe(unittest.TestCase):
    def test_only_recent_items_survive(self):
        items = roundup.parse_feed(RSS.encode(), "Alpha")
        kept = roundup.in_window(items, NOW, 24)
        self.assertEqual([i.title for i in kept], ["Ministers sign water accord"])

    def test_cross_outlet_duplicate_collapses(self):
        items = roundup.parse_feed(RSS.encode(), "Alpha") + roundup.parse_feed(ATOM.encode(), "Beta")
        fresh = roundup.in_window(items, NOW, 24)
        kept = roundup.dedupe(fresh)
        self.assertEqual(len(kept), 2, [i.title for i in kept])

    def test_dedupe_keeps_earliest(self):
        items = roundup.dedupe(roundup.in_window(
            roundup.parse_feed(RSS.encode(), "Alpha") + roundup.parse_feed(ATOM.encode(), "Beta"), NOW, 24))
        water = [i for i in items if "water" in i.title.lower()][0]
        self.assertEqual(water.outlet, "Alpha")


class TestTopicsAndRender(unittest.TestCase):
    def setUp(self):
        self.items, self.failures = roundup.collect(CONFIG, NOW, loader=lambda url: RSS.encode() if "a.example" in url else ATOM.encode())

    def test_topics_assigned(self):
        names = sorted(t for i in self.items for t in i.topics)
        self.assertEqual(names, ["Politics", "Water"])

    def test_render_has_sections_and_items(self):
        doc = roundup.render(self.items, CONFIG, NOW, self.failures)
        self.assertIn("# MEDIA ROUNDUP", doc)
        self.assertIn("## Water", doc)
        self.assertIn("## Politics", doc)
        self.assertIn("**Alpha — Ministers sign water accord**", doc)
        self.assertIn("https://b.example/10", doc)

    def test_render_states_empty_run(self):
        doc = roundup.render([], CONFIG, NOW, [])
        self.assertIn("No items met the freshness window", doc)

    def test_failed_feed_is_reported_not_hidden(self):
        def loader(url):
            if "b.example" in url:
                raise OSError("timeout")
            return RSS.encode()
        items, failures = roundup.collect(CONFIG, NOW, loader=loader)
        doc = roundup.render(items, CONFIG, NOW, failures)
        self.assertIn("Coverage gaps", doc)
        self.assertIn("Beta: feed unreachable", doc)


class TestEndToEnd(unittest.TestCase):
    def test_cli_with_cached_feeds(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            cfg = tmp_path / "watchlist.json"
            cfg.write_text(json.dumps(CONFIG), encoding="utf-8")
            cache = tmp_path / "cache"
            cache.mkdir()
            for url, body in (("https://a.example/rss", RSS), ("https://b.example/atom", ATOM)):
                name = roundup.re.sub(r"[^a-z0-9]+", "-", url.lower()).strip("-")[:80] + ".xml"
                (cache / name).write_text(body, encoding="utf-8")
            out = tmp_path / "roundup.md"
            result = subprocess.run(
                [sys.executable, str(Path(__file__).parent.parent / "roundup.py"),
                 "--config", str(cfg), "--out", str(out), "--cache", str(cache),
                 "--now", "2026-11-12T09:00:00Z"],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Ministers sign water accord", out.read_text())


if __name__ == "__main__":
    unittest.main(verbosity=2)
