"""
youtube-transcript.io client for the Travis Marziani channel.

The /channels endpoint only returns channel *metadata*, not videos.
To enumerate a channel's videos we shell out to yt-dlp (no API key needed)
against the uploads playlist, then feed the IDs into /transcripts.

Usage:
    # Channel metadata (title, desc, keywords)
    python fetch_transcripts.py channel @TravisMarziani

    # List every video ID for the channel (writes video_ids.txt)
    python fetch_transcripts.py list-channel @TravisMarziani

    # Pull transcripts
    python fetch_transcripts.py videos jNQXAC9IVRw dQw4w9WgXcQ
    python fetch_transcripts.py from-file video_ids.txt

    # One-shot: list the channel, then download every transcript
    python fetch_transcripts.py sync @TravisMarziani
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

TOKEN = os.environ["YOUTUBE_TRANSCRIPT_IO_TOKEN"]
BASE = "https://www.youtube-transcript.io/api"
HEADERS = {
    "Authorization": f"Basic {TOKEN}",
    "Content-Type": "application/json",
}

TRANSCRIPTS_DIR = ROOT / "transcripts"
CHANNELS_DIR = ROOT / "channels"
TRANSCRIPTS_DIR.mkdir(exist_ok=True)
CHANNELS_DIR.mkdir(exist_ok=True)


def post(path: str, payload: dict) -> dict:
    r = requests.post(f"{BASE}{path}", headers=HEADERS, json=payload, timeout=60)
    if r.status_code >= 400:
        print(f"[{r.status_code}] {r.text}", file=sys.stderr)
        r.raise_for_status()
    return r.json()


def fetch_channel_meta(channel_id: str) -> dict:
    data = post("/channels", {"ids": [channel_id]})
    out = CHANNELS_DIR / f"{channel_id.lstrip('@')}.json"
    out.write_text(json.dumps(data, indent=2))
    print(f"saved {out}")
    return data


def list_channel_videos(channel_id: str) -> list[str]:
    """Use yt-dlp to enumerate every video ID on a channel."""
    url = f"https://www.youtube.com/{channel_id}/videos" if channel_id.startswith("@") else f"https://www.youtube.com/channel/{channel_id}/videos"
    print(f"listing videos via yt-dlp: {url}")
    result = subprocess.run(
        ["yt-dlp", "--flat-playlist", "--print", "%(id)s", url],
        capture_output=True, text=True, check=True,
    )
    ids = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    out = CHANNELS_DIR / f"{channel_id.lstrip('@')}_video_ids.txt"
    out.write_text("\n".join(ids) + "\n")
    print(f"found {len(ids)} videos, saved {out}")
    return ids


def fetch_transcripts(video_ids: list[str], batch_size: int = 50, skip_existing: bool = True) -> None:
    if skip_existing:
        existing = {p.stem for p in TRANSCRIPTS_DIR.glob("*.json")}
        before = len(video_ids)
        video_ids = [v for v in video_ids if v not in existing]
        if before != len(video_ids):
            print(f"skipping {before - len(video_ids)} already-downloaded transcripts")

    for i in range(0, len(video_ids), batch_size):
        batch = video_ids[i : i + batch_size]
        print(f"batch {i // batch_size + 1}/{(len(video_ids) + batch_size - 1) // batch_size} ({len(batch)} videos)")
        try:
            data = post("/transcripts", {"ids": batch})
        except requests.HTTPError as e:
            print(f"  batch failed: {e} — continuing", file=sys.stderr)
            continue
        items = data if isinstance(data, list) else data.get("transcripts", [])
        for item in items:
            vid = item.get("id") or item.get("videoId") or "unknown"
            out = TRANSCRIPTS_DIR / f"{vid}.json"
            out.write_text(json.dumps(item, indent=2))
        print(f"  saved {len(items)} transcripts")
        time.sleep(1)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("channel", help="fetch channel metadata")
    c.add_argument("channel_id", help="@handle or UC... channel ID")

    lc = sub.add_parser("list-channel", help="list every video ID for a channel (via yt-dlp)")
    lc.add_argument("channel_id")

    v = sub.add_parser("videos", help="fetch transcripts for explicit video IDs")
    v.add_argument("video_ids", nargs="+")

    f = sub.add_parser("from-file", help="fetch transcripts from a newline-delimited file")
    f.add_argument("path")

    s = sub.add_parser("sync", help="list channel + download all transcripts")
    s.add_argument("channel_id")

    args = ap.parse_args()

    if args.cmd == "channel":
        fetch_channel_meta(args.channel_id)
    elif args.cmd == "list-channel":
        list_channel_videos(args.channel_id)
    elif args.cmd == "videos":
        fetch_transcripts(args.video_ids)
    elif args.cmd == "from-file":
        ids = [ln.strip() for ln in Path(args.path).read_text().splitlines() if ln.strip()]
        fetch_transcripts(ids)
    elif args.cmd == "sync":
        fetch_channel_meta(args.channel_id)
        ids = list_channel_videos(args.channel_id)
        fetch_transcripts(ids)


if __name__ == "__main__":
    main()
