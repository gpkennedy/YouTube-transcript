# Transcript Extractor

Extrait la transcription d'une vidéo et la sauvegarde en fichier `.txt`.
Supporte YouTube nativement, 1000+ autres plateformes (Vimeo, Twitch, Dailymotion, etc.) via yt-dlp,
les playlists HLS (`.m3u`/`.m3u8`) locaux, et la transcription audio via Whisper en fallback.

## Installation

```bash
cd youtube-transcript
./setup.sh
```

> Whisper nécessite aussi `ffmpeg` : `brew install ffmpeg`

## Utilisation

```bash
./transcript "<url>" [options] [dossier_sortie]
./transcript fichier.m3u [dossier_sortie]
```

> Les URLs contenant `?` doivent être entre guillemets.

### Options

| Option | Description |
| ------ | ----------- |
| `--lang <code>` | Langue souhaitée (ex: `fr`, `en`) |
| `--generic` | Forcer yt-dlp même pour YouTube |
| `--whisper` | Activer Whisper en fallback si pas de sous-titres |
| `--whisper-model <taille>` | Modèle Whisper à utiliser (défaut : `base`) |

### Exemples

```bash
# YouTube
./transcript "https://www.youtube.com/watch?v=XXXX"
./transcript "https://www.youtube.com/watch?v=XXXX" --lang fr

# Autre plateforme (Vimeo, Twitch, etc.) — auto-détecté
./transcript "https://vimeo.com/123456789" --lang en

# Fallback Whisper si pas de sous-titres
./transcript "https://www.youtube.com/watch?v=XXXX" --whisper

# Whisper avec un modèle plus précis
./transcript "https://www.youtube.com/watch?v=XXXX" --whisper --whisper-model small

# Fichier .m3u local (ex: flux HLS récupéré manuellement)
./transcript rendition.m3u

# Sauvegarder dans un dossier spécifique
./transcript "https://www.youtube.com/watch?v=XXXX" --lang en ./transcriptions
```

### Modèles Whisper

| Modèle | Taille | Vitesse | Précision |
| ------ | ------ | ------- | --------- |
| `tiny` | 75 MB | très rapide | basique |
| `base` | 145 MB | rapide | correct *(défaut)* |
| `small` | 466 MB | moyen | bon |
| `medium` | 1.5 GB | lent | très bon |
| `large` | 3 GB | très lent | meilleur |

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
- Avec `--whisper` : tente les sous-titres en premier, bascule sur Whisper si aucun n'est disponible.
- Whisper tourne entièrement en local, sans API ni coût.

## Limitations

- Sans `--whisper`, la vidéo doit avoir des sous-titres disponibles.
- Whisper peut faire des erreurs sur les noms propres et les chiffres.
- Certaines plateformes (ex: The Economist) sont protégées par Cloudflare — récupérer le fichier `.m3u` manuellement via les DevTools du navigateur.
