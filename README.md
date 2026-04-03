# YouTube Transcript Extractor

Extrait la transcription d'une vidéo YouTube et la sauvegarde en fichier `.txt`.

## Installation

```bash
cd youtube-transcript
python3 -m venv venv
./venv/bin/pip install youtube-transcript-api
```

## Utilisation

```bash
./venv/bin/python transcript.py <url> [--lang <code>] [dossier_sortie]
```

### Exemples

```bash
# Transcription dans la langue d'origine
./venv/bin/python transcript.py "https://www.youtube.com/watch?v=XXXX"

# Transcription en français
./venv/bin/python transcript.py "https://www.youtube.com/watch?v=XXXX" --lang fr

# Transcription en anglais, sauvegardée dans un dossier spécifique
./venv/bin/python transcript.py "https://www.youtube.com/watch?v=XXXX" --lang en ./transcriptions
```

### Codes de langue courants

| Code | Langue     |
|------|------------|
| `fr` | Français   |
| `en` | Anglais    |
| `es` | Espagnol   |
| `de` | Allemand   |
| `it` | Italien    |
| `pt` | Portugais  |

## Comportement

- Le fichier de sortie est nommé `[video_id].txt` et sauvegardé dans le dossier courant par défaut.
- Sans `--lang`, le script choisit automatiquement la meilleure transcription disponible (manuelle > auto-générée), en priorité en français puis anglais.
- Avec `--lang`, le script cherche d'abord une transcription native dans cette langue, sinon utilise la traduction automatique de YouTube.
- Les formats d'URL acceptés : `youtube.com/watch?v=`, `youtu.be/`, `/shorts/`, `/embed/`.

## Limitations

- La vidéo doit avoir des sous-titres activés (manuels ou auto-générés).
- La qualité des transcriptions auto-générées dépend de YouTube.
