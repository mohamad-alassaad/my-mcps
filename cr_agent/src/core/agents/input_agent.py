from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from src.config import AUDIO_EXT, TEXTE_EXT

_MOTS_FORTS = {"objet", "convocation", "invitation"}
_MOTS_NORMAUX = {"ordre du jour", "agenda", "objet", "convocation", "invitation"}


@dataclass
class InputResult:
    texte: str
    source_type: str


class InputAgent:
    def traiter(
        self,
        fichier: Optional[str] = None,
        texte: Optional[str] = None,
        source_hint: str = "auto",
    ) -> InputResult:

        if not fichier and not texte:
            raise ValueError("Aucune entrée fournie.")

        if fichier:
            chemin = Path(fichier)
            if not chemin.exists():
                raise FileNotFoundError(f"Fichier introuvable : {chemin}")

            ext = chemin.suffix.lower()

            if ext in AUDIO_EXT:
                return InputResult(texte=str(chemin), source_type="audio")

            if ext in TEXTE_EXT:
                contenu = self._lire(chemin, ext)
                type_ = (
                    source_hint if source_hint != "auto" else self._detecter(contenu)
                )
                return InputResult(texte=contenu, source_type=type_)

            raise ValueError(f"Format non supporté : {ext}")

        contenu = texte.strip()
        type_ = source_hint if source_hint != "auto" else self._detecter(contenu)
        return InputResult(texte=contenu, source_type=type_)

    def _lire(self, chemin: Path, ext: str) -> str:
        if ext in {".txt", ".md"}:
            return self._lire_texte(chemin)
        if ext == ".pdf":
            return self._lire_pdf(chemin)
        if ext == ".docx":
            return self._lire_docx(chemin)
        raise ValueError(f"Lecteur manquant pour : {ext}")

    def _lire_texte(self, chemin: Path) -> str:
        for enc in ("utf-8", "latin-1", "cp1252"):
            try:
                return chemin.read_text(encoding=enc)
            except UnicodeDecodeError:
                continue
        raise ValueError(f"Encodage non supporté : {chemin}")

    def _lire_pdf(self, chemin: Path) -> str:
        import pypdf

        reader = pypdf.PdfReader(str(chemin))
        return "\n".join(p.extract_text() or "" for p in reader.pages)

    def _lire_docx(self, chemin: Path) -> str:
        import docx

        doc = docx.Document(str(chemin))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

    def _detecter(self, texte: str) -> str:
        tl = texte.lower()
        for mot in _MOTS_FORTS:
            if mot in tl:
                return "invitation"
        count = sum(1 for mot in _MOTS_NORMAUX if mot in tl)
        return "invitation" if count >= 2 else "notes"
