"""
Find transcripts where Travis prices HIS COURSE at $997 or ~$1,000.

Two filters must BOTH pass:
  1. Price-framing verb within ~60 chars BEFORE the dollar amount
     (e.g. "charge", "pay", "cost", "reduced to", "for just/only", "it's")
     This filters out income claims like "he made a thousand dollars".
  2. Course/program context within ~300 chars of the amount.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
TRANSCRIPTS = ROOT / "transcripts"
COURSE_WINDOW = 300    # chars on each side of match for course context
PRICE_VERB_WINDOW = 60 # chars BEFORE the amount for a pricing verb

# Focus on amounts specifically — exclude "thousand dollars" on its own
# unless preceded by "a"/"one" (which implies a singular price, not income)
PRICE_RX = re.compile(
    r"\b(997|\$1,?000|\$1k|1,?000\s+dollars?|"
    r"(?:a|one)\s+thousand\s+dollars?)\b",
    re.IGNORECASE,
)

# Words/phrases that frame the number AS A PRICE
PRICE_VERB_RX = re.compile(
    r"\b(charg\w+|cost\w*|pay(?:ing|s)?|pric\w+|sell(?:ing)?\s+(?:it\s+)?for|"
    r"selling\s+for|reduc\w+|only|just|for\s+just|for\s+only|"
    r"invest(?:ment)?|value|worth|normally|regularly|"
    r"(?:course|program|formula)\s+(?:is|was|for)|"
    r"(?:it'?s|it\s+is|it'?ll\s+be|its?\s+gonna\s+be)\s*(?:only|just)?)\b",
    re.IGNORECASE,
)

# Travis's course / program — his specific offers and generic references
COURSE_RX = re.compile(
    r"\b(my\s+(?:course|program|training)|this\s+(?:course|program|training)|"
    r"the\s+(?:course|program|training)|accelerator|"
    r"passion\s+product\s+formula|"
    r"mastermind|coaching|"
    r"enroll|reserve\s+your\s+spot|"
    r"join\s+(?:the|my|this)\s+(?:course|program|training)|"
    r"members?[-\s]?only|lifetime\s+access|"
    r"money[-\s]?back\s+guarantee|risk[-\s]?free)\b",
    re.IGNORECASE,
)


def window_snippet(text: str, start: int, end: int, pad: int = 250) -> str:
    lo = max(0, start - pad)
    hi = min(len(text), end + pad)
    prefix = "…" if lo > 0 else ""
    suffix = "…" if hi < len(text) else ""
    return f"{prefix}{text[lo:hi].replace(chr(10), ' ').strip()}{suffix}"


def find_hits():
    results = []
    for f in sorted(TRANSCRIPTS.glob("*.json")):
        d = json.loads(f.read_text())
        text = d.get("text", "")
        vid = d.get("id", f.stem)
        title = d.get("title", "(untitled)")

        hits = []
        for m in PRICE_RX.finditer(text):
            # Price-verb must be within the preceding PRICE_VERB_WINDOW chars
            pre_start = max(0, m.start() - PRICE_VERB_WINDOW)
            pre_text = text[pre_start:m.start()]
            price_verb = PRICE_VERB_RX.search(pre_text)
            if not price_verb:
                continue

            # Course context in wider window
            ctx_lo = max(0, m.start() - COURSE_WINDOW)
            ctx_hi = min(len(text), m.end() + COURSE_WINDOW)
            course_context = COURSE_RX.findall(text[ctx_lo:ctx_hi])
            if not course_context:
                continue

            hits.append({
                "price_term": m.group(0),
                "price_verb": price_verb.group(0),
                "course_context": sorted(set(c.lower() for c in course_context)),
                "snippet": window_snippet(text, m.start(), m.end()),
            })
        if hits:
            results.append({
                "id": vid,
                "title": title,
                "url": f"https://youtube.com/watch?v={vid}",
                "hits": hits,
            })
    return results


def highlight(text: str) -> str:
    text = PRICE_RX.sub(lambda m: f"**💰 {m.group(0)}**", text)
    text = PRICE_VERB_RX.sub(lambda m: f"**_{m.group(0)}_**", text)
    text = COURSE_RX.sub(lambda m: f"__{m.group(0)}__", text)
    return text


def render(results):
    total = sum(len(r["hits"]) for r in results)
    lines = [
        "# Travis Course Pricing Mentions (filtered)",
        "",
        f"Videos where Travis quotes a price (**💰**) for his __course/program__, preceded by a _pricing verb_.",
        "",
        f"**{len(results)} videos** • **{total} hits**",
        "",
    ]
    results.sort(key=lambda r: (-len(r["hits"]), r["title"]))
    for r in results:
        lines.append(f"## {r['title']}  _({len(r['hits'])} hit{'s' if len(r['hits']) != 1 else ''})_")
        lines.append(f"<{r['url']}>")
        lines.append("")
        for h in r["hits"]:
            lines.append(f"- **price:** `{h['price_term']}` &nbsp; **verb:** `{h['price_verb']}` &nbsp; **ctx:** {', '.join(h['course_context'])}")
            lines.append(f"  > {highlight(h['snippet'])}")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    results = find_hits()
    out = ROOT / "course_pricing_mentions.md"
    out.write_text(render(results))
    total = sum(len(r["hits"]) for r in results)
    print(f"saved {out.name} — {len(results)} videos, {total} hits")
