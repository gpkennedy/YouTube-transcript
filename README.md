# Transcript Extractor

> [Lire en français](README.fr.md)

Extracts transcripts from videos and saves them as `.txt` files.
Supports YouTube natively, 1000+ other platforms (Vimeo, Twitch, Dailymotion, etc.) via yt-dlp,
local HLS playlists (`.m3u`/`.m3u8`), and audio transcription via Whisper as a fallback.

## Installation

```bash
cd youtube-transcript
./setup.sh
```

> Whisper also requires `ffmpeg`: `brew install ffmpeg`

## Usage

```bash
./transcript "<url>" [options] [output_dir]
./transcript file.m3u [output_dir]
```

> URLs containing `?` must be quoted.

### Options

| Option | Description |
| ------ | ----------- |
| `--lang <code>` | Desired language (e.g. `fr`, `en`) |
| `--generic` | Force yt-dlp even for YouTube |
| `--title <name>` | Custom output filename |
| `--whisper` | Enable Whisper fallback when no subtitles are available |
| `--whisper-model <size>` | Whisper model to use (default: `base`) |

### Examples

```bash
# YouTube
./transcript "https://www.youtube.com/watch?v=XXXX"
./transcript "https://www.youtube.com/watch?v=XXXX" --lang fr

# Other platform (Vimeo, Twitch, etc.) — auto-detected
./transcript "https://vimeo.com/123456789" --lang en

# Whisper fallback when no subtitles are available
./transcript "https://www.youtube.com/watch?v=XXXX" --whisper

# Custom output filename
./transcript "https://www.youtube.com/watch?v=XXXX" --title "Lagarde Conference 2024"

# Whisper with a more accurate model
./transcript "https://www.youtube.com/watch?v=XXXX" --whisper --whisper-model small

# Local .m3u file (e.g. HLS stream retrieved manually via DevTools)
./transcript rendition.m3u

# Save to a specific folder
./transcript "https://www.youtube.com/watch?v=XXXX" --lang en ./transcripts
```

### Whisper Models

| Model | Size | Speed | Accuracy |
| ----- | ---- | ----- | -------- |
| `tiny` | 75 MB | very fast | basic |
| `base` | 145 MB | fast | decent *(default)* |
| `small` | 466 MB | medium | good |
| `medium` | 1.5 GB | slow | very good |
| `large` | 3 GB | very slow | best |

### Common Language Codes

| Code | Language |
| ---- | -------- |
| `fr` | French |
| `en` | English |
| `es` | Spanish |
| `de` | German |
| `it` | Italian |
| `pt` | Portuguese |

## Behaviour

- Output file is named `[id].txt` and saved in the current directory by default.
- Without `--lang`, automatic priority: `fr → en → es → de → it → pt`.
- Manual subtitles take priority over auto-generated ones.
- With `--whisper`: tries subtitles first, falls back to Whisper if none are available.
- Whisper runs entirely locally — no API, no cost.

## Limitations

- Without `--whisper`, the video must have subtitles available.
- Whisper may make errors on proper nouns and numbers.
- Some platforms (e.g. The Economist) are protected by Cloudflare — retrieve the `.m3u` file manually via the browser DevTools.
