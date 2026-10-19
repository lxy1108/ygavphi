#!/usr/bin/env python3
"""Scan audio/ and build feed.xml (RSS 2.0 + iTunes) for GitHub Pages.

Per-episode metadata: optional sidecar audio/<filename-stem>.json with keys
  title, description, pubDate (ISO 8601, e.g. 2026-10-19T23:58:00+08:00)
Falls back to filename + file mtime. GUID = base URL + encoded filename
(isPermaLink=false), so re-runs never duplicate episodes.
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from feedgen.feed import FeedGenerator
from mutagen import File as MutagenFile

ROOT = Path(__file__).resolve().parent
AUDIO_DIR = ROOT / "audio"
BASE_URL = os.environ.get("PODCAST_BASE_URL", "https://lxy1108.github.io/ygavphi/").rstrip("/") + "/"
MIME = {".mp3": "audio/mpeg", ".m4a": "audio/x-m4a"}

CHANNEL = {
    "title": "PaperCast",
    "description": "PaperCast：学术论文英文深度技术解读播客（English technical deep dives into research papers）。",
    "language": "zh-cn",
    "author": "PaperCast",
    "category": "Science",
    "owner_name": "PaperCast",
    "owner_email": os.environ.get("PODCAST_OWNER_EMAIL", ""),  # optional; public if set
}


def fmt_duration(seconds: float) -> str:
    s = int(round(seconds))
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def load_meta(path: Path) -> dict:
    side = path.with_suffix(".json")
    meta = json.loads(side.read_text(encoding="utf-8")) if side.exists() else {}
    if meta.get("pubDate"):
        pub = datetime.fromisoformat(meta["pubDate"])
        if pub.tzinfo is None:
            pub = pub.replace(tzinfo=timezone.utc)
    else:
        pub = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return {
        "title": meta.get("title") or path.stem.replace("-", " ").replace("_", " "),
        "description": meta.get("description") or path.stem,
        "pub": pub,
    }


def main() -> int:
    fg = FeedGenerator()
    fg.load_extension("podcast")
    fg.title(CHANNEL["title"])
    fg.description(CHANNEL["description"])
    fg.link(href=BASE_URL, rel="alternate")
    fg.language(CHANNEL["language"])
    fg.image(url=BASE_URL + "cover.jpg", title=CHANNEL["title"], link=BASE_URL)
    fg.podcast.itunes_author(CHANNEL["author"])
    fg.podcast.itunes_image(BASE_URL + "cover.jpg")
    fg.podcast.itunes_explicit("no")
    fg.podcast.itunes_category(CHANNEL["category"])
    fg.podcast.itunes_summary(CHANNEL["description"])
    if CHANNEL["owner_email"]:
        fg.podcast.itunes_owner(name=CHANNEL["owner_name"], email=CHANNEL["owner_email"])

    files = sorted(p for p in AUDIO_DIR.iterdir() if p.suffix.lower() in MIME)
    episodes = []
    for p in files:
        meta = load_meta(p)
        audio = MutagenFile(p)
        dur = audio.info.length if audio is not None and audio.info else 0
        episodes.append((meta["pub"], p, meta, dur))
    episodes.sort(key=lambda e: e[0])  # feedgen prepends: newest ends up first

    for pub, p, meta, dur in episodes:
        url = BASE_URL + "audio/" + quote(p.name)
        fe = fg.add_entry()
        fe.title(meta["title"])
        fe.description(meta["description"])
        fe.podcast.itunes_summary(meta["description"])
        fe.guid(url, permalink=False)
        fe.pubDate(pub)
        fe.enclosure(url, str(p.stat().st_size), MIME[p.suffix.lower()])
        fe.podcast.itunes_duration(fmt_duration(dur))
        fe.podcast.itunes_explicit("no")

    fg.rss_file(str(ROOT / "feed.xml"), pretty=True)
    print(f"feed.xml written with {len(episodes)} episode(s); base={BASE_URL}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
