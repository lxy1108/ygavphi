#!/usr/bin/env python3
"""One-command episode add: copy audio (mp3 if >90 MB), write sidecar JSON,
regenerate feed.xml, git commit + push.

Example:
  python3 add_episode.py /path/podcast.m4a --slug 2026-10-19-my-paper \
      --title "Paper title" --description "Summary... arXiv: https://arxiv.org/abs/XXXX" \
      [--pubdate 2026-10-19T23:58:00+08:00] [--no-push]
"""
import argparse
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AUDIO = ROOT / "audio"
LIMIT = 90 * 1024 * 1024  # GitHub hard limit is 100 MB per file


def run(cmd):
    print("+", " ".join(map(str, cmd)))
    subprocess.run(cmd, check=True, cwd=ROOT)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("--slug", required=True, help="filename stem, e.g. 2026-10-19-paper-name")
    ap.add_argument("--title", required=True)
    ap.add_argument("--description", required=True)
    ap.add_argument("--pubdate", default=datetime.now().astimezone().isoformat(timespec="seconds"))
    ap.add_argument("--bitrate", default="80k", help="mp3 bitrate when compressing (64k-96k)")
    ap.add_argument("--no-push", action="store_true")
    a = ap.parse_args()

    src = Path(a.audio).expanduser().resolve()
    AUDIO.mkdir(exist_ok=True)
    if src.stat().st_size > LIMIT:
        dest = AUDIO / f"{a.slug}.mp3"
        run(["ffmpeg", "-y", "-i", src, "-vn", "-ac", "1", "-codec:a", "libmp3lame", "-b:a", a.bitrate, dest])
        if dest.stat().st_size > LIMIT:
            raise SystemExit(f"Still >90 MB after compression ({dest.stat().st_size} B); lower --bitrate")
    else:
        ext = src.suffix.lower()
        if ext not in (".mp3", ".m4a"):
            raise SystemExit(f"Unsupported extension {ext}; use mp3 or m4a")
        dest = AUDIO / f"{a.slug}{ext}"
        shutil.copy2(src, dest)

    meta = {"title": a.title, "description": a.description, "pubDate": a.pubdate}
    dest.with_suffix(".json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    run(["python3", "gen_rss.py"])
    run(["git", "add", "audio", "feed.xml"])
    run(["git", "commit", "-m", f"Add episode: {a.title}"])
    if not a.no_push:
        run(["git", "push", "origin", "main"])
    print("Done:", dest.name)


if __name__ == "__main__":
    main()
