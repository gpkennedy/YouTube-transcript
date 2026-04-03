#!/usr/bin/env python3

import sys
import re
import os
import json
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled


def extract_video_id(url: str) -> str:
    patterns = [
        r"(?:v=|/v/|youtu\.be/|/embed/|/shorts/)([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    # Maybe it's already a raw video ID
    if re.match(r"^[a-zA-Z0-9_-]{11}$", url):
        return url
    raise ValueError(f"Impossible d'extraire l'ID de la vidéo depuis : {url}")


def is_youtube_url(url: str) -> bool:
    return bool(re.search(r'(?:youtube\.com|youtu\.be)', url))


def fetch_transcript(video_id: str, lang: str | None = None) -> tuple[str, str]:
    api = YouTubeTranscriptApi()
    transcript_list = api.list(video_id)

    priority = [lang] if lang else ["fr", "en", "es", "de", "it", "pt"]

    try:
        transcript = transcript_list.find_manually_created_transcript(priority)
    except NoTranscriptFound:
        try:
            transcript = transcript_list.find_generated_transcript(priority)
        except NoTranscriptFound:
            # Fallback: take any transcript and translate it
            transcript = next(iter(transcript_list))
            if lang and transcript.is_translatable:
                transcript = transcript.translate(lang)

    entries = transcript.fetch()
    language = transcript.language
    text = " ".join(entry.text for entry in entries)
    return text, language


def parse_json3(content: str) -> str:
    data = json.loads(content)
    texts = []
    for event in data.get('events', []):
        for seg in event.get('segs', []):
            t = seg.get('utf8', '').replace('\n', ' ').strip()
            if t:
                texts.append(t)
    return ' '.join(texts)


def parse_vtt(content: str) -> str:
    texts = []
    for line in content.split('\n'):
        line = line.strip()
        if not line or line.startswith('WEBVTT') or line.startswith('NOTE') or line.startswith('X-TIMESTAMP-MAP') or '-->' in line:
            continue
        if re.match(r'^\d+$', line):
            continue
        line = re.sub(r'<[^>]+>', '', line).strip()
        # Skip consecutive duplicate lines (fréquent dans les sous-titres roulants)
        if line and (not texts or texts[-1] != line):
            texts.append(line)
    return ' '.join(texts)


def fetch_transcript_generic(url: str, lang: str | None = None) -> tuple[str, str, str]:
    """Récupère les sous-titres via yt-dlp (supporte 1000+ plateformes)."""
    try:
        import yt_dlp
    except ImportError:
        raise ImportError(
            "yt-dlp est requis pour les sources non-YouTube.\n"
            "Installez-le avec : pip install yt-dlp"
        )

    priority = [lang] if lang else ["fr", "en", "es", "de", "it", "pt"]

    ydl_opts = {'quiet': True, 'no_warnings': True}

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

        subtitles = info.get('subtitles', {})
        auto_captions = info.get('automatic_captions', {})

        # Sous-titres manuels en priorité, puis auto-générés
        chosen_lang = None
        chosen_formats = None
        is_auto = False

        for lang_code in priority:
            if lang_code in subtitles:
                chosen_lang = lang_code
                chosen_formats = subtitles[lang_code]
                break

        if not chosen_lang:
            for lang_code in priority:
                if lang_code in auto_captions:
                    chosen_lang = lang_code
                    chosen_formats = auto_captions[lang_code]
                    is_auto = True
                    break

        if not chosen_lang:
            # Prendre n'importe quel sous-titre disponible
            if subtitles:
                chosen_lang = next(iter(subtitles))
                chosen_formats = subtitles[chosen_lang]
            elif auto_captions:
                chosen_lang = next(iter(auto_captions))
                chosen_formats = auto_captions[chosen_lang]
                is_auto = True
            else:
                raise ValueError("Aucun sous-titre disponible pour cette URL.")

        # Choisir le meilleur format disponible
        fmt_priority = ['json3', 'vtt', 'srv3', 'ttml', 'srv2', 'srv1']
        sub_url = None
        sub_ext = None

        for ext in fmt_priority:
            for fmt in chosen_formats:
                if fmt.get('ext') == ext:
                    sub_url = fmt['url']
                    sub_ext = ext
                    break
            if sub_url:
                break

        if not sub_url and chosen_formats:
            sub_url = chosen_formats[0]['url']
            sub_ext = chosen_formats[0].get('ext', 'vtt')

        if not sub_url:
            raise ValueError("Impossible de récupérer l'URL des sous-titres.")

        response = ydl.urlopen(sub_url)
        content = response.read().decode('utf-8')

        if sub_ext == 'json3':
            text = parse_json3(content)
        else:
            text = parse_vtt(content)

        lang_label = f"{chosen_lang} (auto)" if is_auto else chosen_lang

        identifier = re.sub(r'[^\w-]', '_', info.get('id', ''))[:50]
        if not identifier:
            import hashlib
            identifier = hashlib.md5(url.encode()).hexdigest()[:12]

        return text, lang_label, identifier


def fetch_transcript_from_m3u(m3u_path: str) -> tuple[str, str]:
    """Parse un fichier .m3u8 local listant des segments .vtt et retourne le texte."""
    import urllib.request

    with open(m3u_path, encoding="utf-8") as f:
        lines = f.read().splitlines()

    urls = [l for l in lines if l.startswith("https://") or l.startswith("http://")]
    if not urls:
        raise ValueError(f"Aucune URL trouvée dans {m3u_path}")

    print(f"{len(urls)} segments trouvés, téléchargement...")
    all_texts = []
    for i, url in enumerate(urls):
        print(f"\r  {i+1}/{len(urls)}", end="", flush=True)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            content = r.read().decode("utf-8")
        segment_text = parse_vtt(content)
        for word in segment_text.split():
            if not all_texts or all_texts[-1] != word:
                all_texts.append(word)
    print()

    identifier = os.path.splitext(os.path.basename(m3u_path))[0]
    return " ".join(all_texts), identifier


def transcribe_with_whisper(url: str, lang: str | None = None, model_size: str = "base") -> tuple[str, str, str]:
    """Transcrit l'audio via Whisper quand aucun sous-titre n'est disponible."""
    try:
        import whisper
    except ImportError:
        raise ImportError(
            "openai-whisper est requis pour la transcription audio.\n"
            "Installez-le avec : pip install openai-whisper"
        )
    try:
        import yt_dlp
    except ImportError:
        raise ImportError("yt-dlp est requis. Installez-le avec : pip install yt-dlp")

    import tempfile
    import glob as globmod

    with tempfile.TemporaryDirectory() as tmpdir:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(tmpdir, 'audio.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}],
        }
        print("Téléchargement de l'audio...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            identifier = re.sub(r'[^\w-]', '_', info.get('id', ''))[:50]
            if not identifier:
                import hashlib
                identifier = hashlib.md5(url.encode()).hexdigest()[:12]

        audio_files = globmod.glob(os.path.join(tmpdir, 'audio.*'))
        if not audio_files:
            raise ValueError("Impossible de télécharger l'audio.")

        print(f"Transcription avec Whisper (modèle : {model_size})...")
        model = whisper.load_model(model_size)
        result = model.transcribe(audio_files[0], language=lang, fp16=False)

    text = result['text'].strip()
    detected_lang = result.get('language', lang or 'unknown')
    return text, f"{detected_lang} (whisper)", identifier


def get_video_title(url: str) -> str | None:
    try:
        import yt_dlp
        ydl_opts = {'quiet': True, 'no_warnings': True, 'skip_download': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('title')
    except Exception:
        return None


def sanitize_filename(title: str) -> str:
    title = re.sub(r'[<>:"/\\|?*]', '', title)
    title = re.sub(r'\s+', '_', title.strip())
    return title[:100]


def save_transcript(text: str, identifier: str, output_dir: str = ".") -> str:
    filename = os.path.join(output_dir, f"{identifier}.txt")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)
    return filename


def main():
    if len(sys.argv) < 2:
        print("Usage: python transcript.py <url|fichier.m3u> [--lang fr] [--generic] [--whisper] [--whisper-model base] [dossier_sortie]")
        print("Exemples:")
        print("  python transcript.py https://www.youtube.com/watch?v=dQw4w9WgXcQ --lang fr")
        print("  python transcript.py https://vimeo.com/123456789")
        print("  python transcript.py rendition.m3u")
        print("  python transcript.py https://... --whisper --whisper-model small")
        sys.exit(1)

    url = sys.argv[1]
    lang = None
    output_dir = "."
    force_generic = False
    use_whisper = False
    whisper_model = "base"
    use_title = False

    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == "--lang" and i + 1 < len(args):
            lang = args[i + 1]
            i += 2
        elif args[i] == "--generic":
            force_generic = True
            i += 1
        elif args[i] == "--whisper":
            use_whisper = True
            i += 1
        elif args[i] == "--whisper-model" and i + 1 < len(args):
            whisper_model = args[i + 1]
            i += 2
        elif args[i] == "--title":
            use_title = True
            i += 1
        else:
            output_dir = args[i]
            i += 1

    os.makedirs(output_dir, exist_ok=True)

    is_local_m3u = os.path.isfile(url) and url.endswith(('.m3u', '.m3u8'))
    use_generic = force_generic or not is_youtube_url(url)

    def whisper_fallback(reason: str) -> tuple[str, str, str]:
        print(f"{reason}")
        print("Fallback sur Whisper...")
        return transcribe_with_whisper(url, lang, whisper_model)

    try:
        if is_local_m3u:
            print(f"Lecture du fichier M3U : {url}")
            text, identifier = fetch_transcript_from_m3u(url)
            language = "en"
        elif use_generic:
            print("Récupération des sous-titres (source générique via yt-dlp)...")
            try:
                text, language, identifier = fetch_transcript_generic(url, lang)
            except ValueError as e:
                if use_whisper:
                    text, language, identifier = whisper_fallback(f"Pas de sous-titres : {e}")
                else:
                    raise
            print(f"Identifiant : {identifier}")
        else:
            video_id = extract_video_id(url)
            identifier = video_id
            print(f"ID vidéo : {video_id}")
            print("Récupération de la transcription...")
            try:
                text, language = fetch_transcript(video_id, lang)
            except Exception as e:
                if use_whisper:
                    text, language, identifier = whisper_fallback(f"Sous-titres YouTube indisponibles ({type(e).__name__}).")
                else:
                    raise

        if use_title and not is_local_m3u:
            title = get_video_title(url)
            if title:
                identifier = sanitize_filename(title)
                print(f"Titre : {title}")

        filename = save_transcript(text, identifier, output_dir)
        print(f"Langue : {language}")
        print(f"Transcription sauvegardée : {filename}")
        print(f"Nombre de mots : {len(text.split())}")

    except ImportError as e:
        print(f"Erreur : {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Erreur : {e}")
        sys.exit(1)
    except TranscriptsDisabled:
        print("Erreur : les transcriptions sont désactivées. Relancez avec --whisper pour transcrire l'audio.")
        sys.exit(1)
    except NoTranscriptFound:
        print("Erreur : aucune transcription disponible. Relancez avec --whisper pour transcrire l'audio.")
        sys.exit(1)
    except Exception as e:
        print(f"Erreur inattendue : {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
