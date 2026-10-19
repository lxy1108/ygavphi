# PaperCast feed

Feed: `feed.xml`. Add an episode (on the box, in this folder):

```bash
python3 add_episode.py /path/to/podcast.m4a --slug YYYY-MM-DD-short-name \
  --title "Episode title" --description "Summary + arXiv link"
```

Audio >90 MB is converted to mp3 (default 80 kbps) automatically. Requires `feedgen`, `mutagen`, `ffmpeg`.

Rules: slug = lowercase/digits/hyphens; existing slug is refused unless `--force`; mp3 bitrate 64k–96k; GUID = `papercast-<slug>` (stable across re-runs). `--no-push` to commit locally only.
