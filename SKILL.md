---
name: media-roundup
description: Use to build a daily media brief from a watchlist.
---

# Media roundup

A daily media brief is read in four minutes by someone who will then speak in public. Everything in it must be true, everything true must be attributable, and everything attributable must have a link. The failure mode is not a missed story; it is a confident sentence with no source behind it.

This skill pairs with `roundup.py` in this repository: the script collects, you decide.

## The pipeline

1. **Window.** Decide the cut-off before you look at anything (default 24 hours). A brief that quietly includes a four-day-old item is a brief that will be corrected in the room.
2. **Collect.** Run the script against the watchlist. Read the coverage gaps section first: a missing outlet changes what the brief can claim.
3. **Triage.** For each item decide one of four things: lead, mention, hold, drop. The test is not importance in the abstract; it is whether the person you are briefing must know it before their first meeting.
4. **Read before you write.** Open the item. A headline is not a story, and a wire headline is frequently wrong in the first hour.
5. **Write the brief** in the shape below.
6. **Check the edges.** Confirm every link resolves, every name is spelled as the outlet spelled it, and every figure you repeat is the figure in the source.

## Shape of the brief

```
CLASSIFICATION LINE (if required)
Date · Window · Outlets scanned · Items

1. LEAD ITEM — two sentences: what happened, why it matters to us.
2. BY TOPIC — one line per item, outlet in bold, link on the line below.
3. WHAT CHANGED — items that revise yesterday's picture. Omit if nothing did.
4. COVERAGE GAPS — outlets that failed, topics with no coverage.
```

Numbered, never a wall of prose. If a section has one item, keep the section: the reader learns the shape and reads faster next time.

## Fidelity rules

- **Attribute every claim to the outlet that made it**, not to "reports". If two outlets conflict, both stand, with the conflict visible.
- **Never merge two outlets into one sentence.** That is how unverified details become agreed facts.
- **Translate only what you can translate.** Where an item is in another language, quote the original title and give a translation in brackets, marked as a translation.
- **No adjective the source did not use.** "Devastating", "historic", "unprecedented" are the outlet's words or they are absent.
- **If the link is dead or paywalled, say so.** Do not cite a page you could not read.
- **Do not summarise a story from its headline and a search snippet.** Open it, or drop it.

## What belongs in a brief and what does not

Include: decisions, appointments, statements by named officials, published data, incidents with confirmed facts, opinion pieces that set a line worth knowing.

Exclude: speculation presented as reporting, aggregated listicles, anything you cannot date within the window, and anything whose inclusion would tell a reader more about your interests than about the day.

## Arabic language items

- Keep the original headline; put the English rendering in brackets.
- Check the outlet's own transliteration of names and places before you render them.
- A wire translation is not the Arabic source. Cite the Arabic outlet when that is where the story broke.

## Delivery

- One page, or two at most. If it needs three, you are reporting rather than briefing.
- Same order every day, so the reader's eye knows where to go.
- Send at a fixed hour. A brief that arrives at a random time is read at a random time.
- Record the run: window, outlets scanned, item count, gaps. When a story is missed, that record is what lets you say why.

## Pitfalls

- **Treating the digest as the brief.** The script output is raw material with timestamps, not a document anyone should receive.
- **Smoothing a contradiction** because one version is more convenient.
- **Adding a story you did not verify** because the brief looked thin. A short honest brief beats a full one with one invented line.
