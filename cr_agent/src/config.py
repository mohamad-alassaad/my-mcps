import configparser
from pathlib import Path
import os

_conf = configparser.ConfigParser()
_conf.read(Path(__file__).parent / "meetscribe.conf", encoding="utf-8")


def _get(section, key, fallback=""):
    return _conf.get(section, key, fallback=fallback)


def _getbool(section, key, fallback=False):
    return _conf.getboolean(section, key, fallback=fallback)


def _getint(section, key, fallback=0):
    return _conf.getint(section, key, fallback=fallback)


BASE_DIR = Path(__file__).parent
EXPORTS_DIR = BASE_DIR / _get("export", "dossier", "exports")
EXPORTS_DIR.mkdir(exist_ok=True)

WHISPER = {
    "modele": _get("whisper", "modele", "tiny"),
    "device": _get("whisper", "device", "cpu"),
    "compute_type": _get("whisper", "compute_type", "int8"),
    "beam_size": _getint("whisper", "beam_size", 5),
    "vad_filter": _getbool("whisper", "vad_filter", True),
    "vad_silence_ms": _getint("whisper", "vad_min_silence_ms", 500),
}

AUDIO_EXT = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".mp4"}
TEXTE_EXT = {".txt", ".md", ".pdf", ".docx"}

OLLAMA = {
    "base_url": os.environ.get(
        "OLLAMA_HOST", _get("ollama", "base_url", "http://localhost:11434")
    ),
    "timeout_conn": _getint("ollama", "timeout_connexion", 3),
    "timeout_gen": _getint("ollama", "timeout_generation", 300),
    "temperature": float(_get("ollama", "temperature", "0.1")),
    "num_predict": _getint("ollama", "num_predict", 1500),
    "modeles_preferes": [
        m.strip() for m in _get("ollama", "modeles_preferes", "mistral").split(",")
    ],
}

EXPORT = {
    "titre_max_chars": _getint("export", "titre_max_chars", 40),
    "txt_largeur": _getint("export", "txt_largeur", 65),
}

PDF = {
    k: _get("pdf", k, v)
    for k, v in {
        "couleur_fond": "0d1117",
        "couleur_surface": "161b22",
        "couleur_accent": "58d1a8",
        "couleur_titre": "f78166",
        "couleur_texte": "e6edf3",
        "couleur_discret": "8b949e",
        "couleur_grille": "30363d",
        "couleur_rouge": "f85149",
        "couleur_violet": "bc8cff",
    }.items()
}

UI = {
    "host": _get("interface", "host", "0.0.0.0"),
    "port": _getint("interface", "port", 7860),
    "titre": _get("interface", "titre", "MeetScribe"),
    "langues": ["fr", "en", "es", "de", "ar"],
    "formats": ["PDF", "Word", "Texte", "Tous"],
}

FORMAT_MAP = {
    "PDF": ["pdf"],
    "Word": ["word"],
    "Texte": ["txt"],
    "Tous": ["pdf", "word", "txt"],
}
