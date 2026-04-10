from typing import Optional, Callable

from src.config import FORMAT_MAP
from src.core.agents.input_agent import InputAgent
from src.core.agents.stt_agent import STTAgent
from src.core.agents.analyzer_agent import AnalyzerAgent, MeetingData
from src.core.agents.writer_agent import WriterAgent
from src.core.agents.generator_agent import GeneratorAgent


class Orchestrator:
    def __init__(self):
        self._input = InputAgent()
        self._stt = STTAgent()
        self._analyzer = AnalyzerAgent()
        self._writer = WriterAgent()
        self._generator = GeneratorAgent()

    def run(
        self,
        fichier: Optional[str] = None,
        texte: Optional[str] = None,
        source_hint: str = "auto",
        langue: str = "fr",
        formats: Optional[list] = None,
        progress_fn: Optional[Callable] = None,
    ) -> dict:

        if not fichier and not texte:
            raise ValueError("Aucune entrée fournie.")

        formats = formats or FORMAT_MAP["Tous"]

        def log(e, msg):
            print(f"[{e}/4] {msg}")
            if progress_fn:
                progress_fn(e, msg)

        log(1, "Lecture...")
        inp = self._input.traiter(fichier=fichier, texte=texte, source_hint=source_hint)

        donnees = MeetingData()
        transcription = ""

        if inp.source_type == "audio":
            log(2, "Transcription...")
            stt = self._stt.transcrire(inp.texte, langue)
            transcription = stt.texte
            donnees.duree = f"{round(stt.duree_s / 60, 1)} min"
            texte_analyse = transcription
        else:
            log(2, "Préparation...")
            texte_analyse = inp.texte

        log(3, "Analyse...")
        donnees = self._analyzer.analyser(texte_analyse, inp.source_type, donnees)

        log(4, "Export...")
        markdown = self._writer.rediger(donnees)
        fichiers = self._generator.generer(markdown, donnees, formats)

        return {
            "markdown": markdown,
            "transcription": transcription,
            "fichiers": fichiers,
            "donnees": donnees,
        }

    def run_cr(
        self,
        fichier_invitation: Optional[str] = None,
        texte_invitation: Optional[str] = None,
        fichier_contenu: Optional[str] = None,
        texte_contenu: Optional[str] = None,
        langue: str = "fr",
        formats: Optional[list] = None,
        progress_fn: Optional[Callable] = None,
    ) -> dict:

        formats = formats or FORMAT_MAP["Tous"]

        def log(e, msg):
            print(f"[exécution {e}/4] {msg}")
            if progress_fn:
                progress_fn(e, msg)

        donnees_inv = MeetingData()
        if fichier_invitation or texte_invitation:
            log(1, "Analyse invitation...")
            inp_inv = self._input.traiter(
                fichier=fichier_invitation,
                texte=texte_invitation,
                source_hint="invitation",
            )
            donnees_inv = self._analyzer.analyser(inp_inv.texte, "invitation")

        transcription = ""
        donnees_contenu = MeetingData()

        if fichier_contenu or texte_contenu:
            log(2, "Analyse contenu...")
            inp_cont = self._input.traiter(
                fichier=fichier_contenu,
                texte=texte_contenu,
                source_hint="notes",
            )
            if inp_cont.source_type == "audio":
                log(2, "Transcription...")
                stt = self._stt.transcrire(inp_cont.texte, langue)
                transcription = stt.texte
                texte_analyse = transcription
                donnees_contenu.duree = f"{round(stt.duree_s / 60, 1)} min"
            else:
                texte_analyse = inp_cont.texte

            donnees_contenu = self._analyzer.analyser(texte_analyse, "notes")

        log(3, "Fusion...")
        donnees = self._analyzer.fusionner(donnees_inv, donnees_contenu)

        log(4, "Export...")
        markdown = self._writer.rediger(donnees)
        fichiers = self._generator.generer(markdown, donnees, formats)

        return {
            "markdown": markdown,
            "transcription": transcription,
            "fichiers": fichiers,
            "donnees": donnees,
        }
