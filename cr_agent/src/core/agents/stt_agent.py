from dataclasses import dataclass
from pathlib import Path

from src.config import WHISPER, AUDIO_EXT


@dataclass
class STTResult:
    texte: str
    langue: str = "fr"
    duree_s: float = 0.0


class STTAgent:
    MODELES_VALIDES = {"tiny", "base", "small", "medium", "large"}

    def __init__(self, modele: str = None):
        nom = modele or WHISPER["modele"]
        if nom not in self.MODELES_VALIDES:
            raise ValueError(f"Modèle Whisper invalide : {nom}")
        self._nom = nom
        self._modele = None  # lazy loading

    def transcrire(self, chemin_audio: str, langue: str = "fr") -> STTResult:
        chemin = Path(chemin_audio)

        if not chemin.exists():
            raise FileNotFoundError(f"Audio introuvable : {chemin}")
        if chemin.suffix.lower() not in AUDIO_EXT:
            raise ValueError(f"Format non supporté : {chemin.suffix}")

        if self._modele is None:
            from faster_whisper import WhisperModel

            self._modele = WhisperModel(
                self._nom,
                device=WHISPER["device"],
                compute_type=WHISPER["compute_type"],
            )

        segments_iter, info = self._modele.transcribe(
            str(chemin),
            language=langue,
            beam_size=WHISPER["beam_size"],
            vad_filter=WHISPER["vad_filter"],
            vad_parameters={"min_silence_duration_ms": WHISPER["vad_silence_ms"]},
        )
        segments = list(segments_iter)
        texte = " ".join(s.text.strip() for s in segments)
        duree = segments[-1].end if segments else 0.0

        return STTResult(texte=texte, langue=info.language, duree_s=duree)
