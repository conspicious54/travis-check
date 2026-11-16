"""
Search transcripts for pattern matches with context.

Usage:
    python search_transcripts.py "997|1,?000|thousand dollar|a thousand"
    python search_transcripts.py "997" --out price_mentions.md
"""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
TRANSCRIPTS = ROOT / "transcripts"
CONTEXT = 120  # chars on each side of match


def search(pattern: str, context: int = CONTEXT):
    rx = re.compile(pattern, re.IGNORECASE)
    hits = []
    for f in sorted(TRANSCRIPTS.glob("*.json")):
        data = json.loads(f.read_text())
        text = data.get("text", "")
        title = data.get("title", "(untitled)")
        vid = data.get("id", f.stem)
        matches = list(rx.finditer(text))
        if not matches:
            continue
        snippets = []
        for m in matches:
            lo = max(0, m.start() - context)
            hi = min(len(text), m.end() + context)
            prefix = "…" if lo > 0 else ""
            suffix = "…" if hi < len(text) else ""
            snippet = text[lo:hi].replace("\n", " ").strip()
            snippets.append(f"{prefix}{snippet}{suffix}")
        hits.append({"id": vid, "title": title, "matches": len(matches), "snippets": snippets})
    return hits


def render_markdown(pattern: str, hits: list) -> str:
    total_matches = sum(h["matches"] for h in hits)
    lines = [
        f"# Transcript search: `{pattern}`",
        "",
        f"**{len(hits)} videos** with **{total_matches} total matches**",
        "",
    ]
    hits.sort(key=lambda h: -h["matches"])
    for h in hits:
        url = f"https://youtube.com/watch?v={h['id']}"
        lines.append(f"## {h['title']} ({h['matches']} matches)")
        lines.append(f"<{url}>")
        lines.append("")
        for s in h["snippets"]:
            # bold the actual matched term
            highlighted = re.sub(
                rf"({pattern})", r"**\1**", s, flags=re.IGNORECASE
            )
            lines.append(f"- {highlighted}")
        lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pattern", help="regex pattern (case-insensitive)")
    ap.add_argument("--out", help="write markdown report to this file")
    ap.add_argument("--context", type=int, default=CONTEXT)
    args = ap.parse_args()

    hits = search(args.pattern, args.context)
    report = render_markdown(args.pattern, hits)

    if args.out:
        Path(args.out).write_text(report)
        print(f"saved {args.out} — {len(hits)} videos, {sum(h['matches'] for h in hits)} matches")
    else:
        print(report)


if __name__ == "__main__":
    main()
