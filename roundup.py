#!/usr/bin/env python3
"""Build a structured media digest from RSS and Atom feeds.

Collects items inside a time window, drops duplicates, groups them by topic
from a keyword map, and writes a markdown briefing. No dependencies.

    python3 roundup.py --config watchlist.json --out roundup.md

The script does not summarise. Deciding what an item means is the job of
whoever signs the briefing; the script only decides what belongs in it.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from email.utils import parsedate_to_datetime
from pathlib import Path

USER_AGENT = "media-roundup/1.0 (+https://github.com/sadok-ayari/media-roundup)"
ATOM = "{http://www.w3.org/2005/Atom}"


@dataclass
class Item:
    outlet: str
    title: str
    link: str
    published: datetime
    summary: str = ""
    topics: list[str] = field(default_factory=list)


def _text(node, *paths):
    for path in paths:
        found = node.find(path)
        if found is not None and (found.text or "").strip():
            return found.text.strip()
    return ""


def _parse_date(raw: str) -> datetime | None:
    if not raw:
        return None
    try:
        dt = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def parse_feed(xml_bytes: bytes, outlet: str) -> list[Item]:
    """Parse RSS 2.0 or Atom into items. Bad XML yields an empty list."""
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return []

    items: list[Item] = []

    for node in root.iter("item"):  # RSS
        published = _parse_date(_text(node, "pubDate", "date"))
        if published is None:
            continue
        items.append(
            Item(
                outlet=outlet,
                title=_text(node, "title"),
                link=_text(node, "link"),
                published=published,
                summary=_text(node, "description", "summary"),
            )
        )

    for node in root.iter(f"{ATOM}entry"):  # Atom
        published = _parse_date(_text(node, f"{ATOM}published", f"{ATOM}updated"))
        if published is None:
            continue
        link = ""
        for candidate in node.findall(f"{ATOM}link"):
            if candidate.get("rel", "alternate") == "alternate":
                link = candidate.get("href", "")
                break
        items.append(
            Item(
                outlet=outlet,
                title=_text(node, f"{ATOM}title"),
                link=link,
                published=published,
                summary=_text(node, f"{ATOM}summary", f"{ATOM}content"),
            )
        )

    return [i for i in items if i.title]


def normalise(title: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", title.lower()).strip()


def dedupe(items: list[Item], threshold: float = 0.85) -> list[Item]:
    """Drop repeats of the same story across outlets, keeping the earliest."""
    kept: list[Item] = []
    for item in sorted(items, key=lambda i: i.published):
        key = normalise(item.title)
        duplicate = False
        for other in kept:
            if item.link and item.link == other.link:
                duplicate = True
                break
            if SequenceMatcher(None, key, normalise(other.title)).ratio() >= threshold:
                duplicate = True
                break
        if not duplicate:
            kept.append(item)
    return kept


def assign_topics(items: list[Item], topics: list[dict]) -> list[Item]:
    for item in items:
        haystack = f"{item.title} {item.summary}".lower()
        matched = [t["name"] for t in topics if any(k.lower() in haystack for k in t.get("keywords", []))]
        item.topics = matched or ["Other"]
    return items


def in_window(items: list[Item], now: datetime, hours: int) -> list[Item]:
    cutoff = now - timedelta(hours=hours)
    return [i for i in items if cutoff <= i.published <= now + timedelta(minutes=5)]


def fetch(url: str, timeout: int = 20) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def collect(config: dict, now: datetime, loader=None) -> tuple[list[Item], list[str]]:
    """Return items in the window plus the outlets that failed."""
    loader = loader or (lambda url: fetch(url))
    hours = int(config.get("window_hours", 24))
    collected: list[Item] = []
    failures: list[str] = []

    for feed in config.get("feeds", []):
        try:
            collected.extend(parse_feed(loader(feed["url"]), feed["outlet"]))
        except Exception:
            failures.append(feed["outlet"])

    items = in_window(collected, now, hours)
    items = dedupe(items)
    return assign_topics(items, config.get("topics", [])), failures


def render(items: list[Item], config: dict, now: datetime, failures: list[str]) -> str:
    title = config.get("title", "MEDIA ROUNDUP")
    order = [t["name"] for t in config.get("topics", [])] + ["Other"]
    lines = [f"# {title}", "", now.strftime("%A, %d %B %Y").lstrip("0"), ""]

    classification = config.get("classification")
    if classification:
        lines += [f"*{classification}*", ""]

    if not items:
        lines += ["No items met the freshness window for this run.", ""]

    for topic in order:
        group = sorted([i for i in items if topic in i.topics], key=lambda i: i.published, reverse=True)
        if not group:
            continue
        lines += [f"## {topic}", ""]
        for item in group:
            stamp = item.published.strftime("%d %b %H:%M UTC")
            lines.append(f"- **{item.outlet} — {item.title}** ({stamp})")
            if item.link:
                lines.append(f"  {item.link}")
        lines.append("")

    if failures:
        lines += ["## Coverage gaps", ""]
        lines += [f"- {name}: feed unreachable this run" for name in sorted(set(failures))]
        lines.append("")

    lines += [
        "---",
        "",
        f"*{len(items)} items, window {config.get('window_hours', 24)}h. Summaries are not generated: "
        "read the source before you brief on it.*",
        "",
    ]
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Build a media digest from RSS and Atom feeds.")
    parser.add_argument("--config", required=True, help="path to watchlist JSON")
    parser.add_argument("--out", default="-", help="output markdown file, or - for stdout")
    parser.add_argument("--hours", type=int, help="override window_hours")
    parser.add_argument("--cache", help="directory of saved .xml files instead of the network")
    parser.add_argument("--now", help="ISO timestamp to treat as now (reproducible runs)")
    args = parser.parse_args(argv)

    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    if args.hours:
        config["window_hours"] = args.hours

    loader = None
    if args.cache:
        cache = Path(args.cache)

        def loader(url: str) -> bytes:
            name = re.sub(r"[^a-z0-9]+", "-", url.lower()).strip("-")[:80] + ".xml"
            return (cache / name).read_bytes()

    now = datetime.fromisoformat(args.now.replace("Z", "+00:00")) if args.now else datetime.now(timezone.utc)
    items, failures = collect(config, now, loader)
    document = render(items, config, now, failures)

    if args.out == "-":
        print(document)
    else:
        Path(args.out).write_text(document, encoding="utf-8")
        print(f"{len(items)} items -> {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
