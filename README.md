# Transcript Extractor

Extrait la transcription d'une vidéo et la sauvegarde en fichier `.txt`.
Supporte YouTube nativement, et 1000+ autres plateformes (Vimeo, Twitch, Dailymotion, etc.) via yt-dlp.
Supporte aussi les playlists HLS (fichiers `.m3u`/`.m3u8`) locaux.

## Installation

```bash
cd youtube-transcript
python3 -m venv venv
./venv/bin/pip install youtube-transcript-api yt-dlp
```

## Utilisation

```bash
./transcript "<url>" [--lang <code>] [--generic] [dossier_sortie]
./transcript fichier.m3u [dossier_sortie]
```

> Les URLs contenant `?` doivent être entre guillemets.

### Exemples

```bash
# YouTube
./transcript "https://www.youtube.com/watch?v=XXXX"
./transcript "https://www.youtube.com/watch?v=XXXX" --lang fr

# Autre plateforme (Vimeo, Twitch, etc.) — auto-détecté
./transcript "https://vimeo.com/123456789" --lang en

# Forcer yt-dlp même pour YouTube
./transcript "https://www.youtube.com/watch?v=XXXX" --generic

# Fichier .m3u local (ex: flux HLS récupéré manuellement)
./transcript rendition.m3u

# Sauvegarder dans un dossier spécifique
./transcript "https://www.youtube.com/watch?v=XXXX" --lang en ./transcriptions
```

### Codes de langue courants

| Code | Langue    |
|------|-----------|
| `fr` | Français  |
| `en` | Anglais   |
| `es` | Espagnol  |
| `de` | Allemand  |
| `it` | Italien   |
| `pt` | Portugais |

## Comportement

- Le fichier de sortie est nommé `[id].txt` et sauvegardé dans le dossier courant par défaut.
- Sans `--lang`, priorité automatique : `fr → en → es → de → it → pt`.
- Sous-titres manuels prioritaires sur les auto-générés.
- Pour les sources non-YouTube sans sous-titres dans les langues demandées, fallback sur n'importe quelle langue disponible.

## Limitations

- La vidéo doit avoir des sous-titres activés (manuels ou auto-générés).
- Certaines plateformes (ex: The Economist) sont protégées par Cloudflare — récupérer le fichier `.m3u` manuellement via les DevTools du navigateur.
