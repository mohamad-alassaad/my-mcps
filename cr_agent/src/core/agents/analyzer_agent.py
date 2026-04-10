# agents/analyzer_agent.py
"""
Analyzer Agent — Stratégie optimale pour llama3.2:1b :
Prompt unique → sortie Markdown structurée → parser Markdown robuste.
Le modèle produit naturellement du Markdown, on exploite ça.
Fallback heuristique si Ollama absent/timeout.
"""

import re
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import requests


from src.config import OLLAMA


_RE_DATE = re.compile(
    r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"
    r"|\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|"
    r"août|septembre|octobre|novembre|décembre)\s+\d{4})\b",
    re.IGNORECASE,
)
_RE_BRUIT = re.compile(
    r"\b(euh+|hmm+|bah\b|du coup|ouais|hein\b|voilà|ben\b|"
    r"c'est-à-dire|je veux dire|en fait|t'as|tu vois)\b",
    re.IGNORECASE,
)
_RE_LOCUTEUR = re.compile(r"^[A-ZÉÀÈÊÂ][A-ZÉÀÈÊÂ\s]{5,}$", re.MULTILINE)
_RE_TIMESTAMP = re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b")
_RE_SYSTEME = re.compile(
    r"^.*(a commencé la transcription|arrêt de la transcription"
    r"|a rejoint|a quitté|est en ligne|est hors ligne).*$",
    re.IGNORECASE | re.MULTILINE,
)

_PLACEHOLDERS = {
    "sujet 1",
    "sujet 2",
    "sujet 3",
    "point 1",
    "point 2",
    "decision 1",
    "etape 1",
    "etape 2",
    "tache",
    "action 1",
    "titre court",
    "titre de la reunion",
    "analyse de la transcription",
    "resume de la reunion",
    "2 phrases",
    "prenom",
    "prenom nom",
    "faire des transcriptions",
    "l'écriture de transcriptions",
    "n/a",
    "na",
    "vide",
    "aucun",
    "aucune",
    "none",
    "null",
    "",
}


@dataclass
class Action:
    texte: str
    responsable: str = "À définir"
    echeance: str = ""
    priorite: str = "normale"


@dataclass
class MeetingData:
    titre: str = ""
    date: str = ""
    lieu: str = ""
    organisateur: str = ""
    participants: list = field(default_factory=list)
    duree: str = ""
    ordre_du_jour: list = field(default_factory=list)
    resume: str = ""
    points_discutes: list = field(default_factory=list)
    decisions: list = field(default_factory=list)
    actions: list = field(default_factory=list)
    prochaines_etapes: list = field(default_factory=list)
    source_type: str = ""


class AnalyzerAgent:
    def __init__(self):
        self._modele_cache: Optional[str] = None

    # ── Point d'entrée

    def analyser(
        self,
        texte: str,
        source_type: str = "notes",
        base: Optional[MeetingData] = None,
    ) -> MeetingData:
        donnees = base or MeetingData()
        donnees.source_type = source_type

        texte_propre = self._nettoyer_oral(texte)

        modele = self._detecter_modele()
        if modele:
            print(f"[Analyzer] Ollama → {modele}")
            return self._avec_ollama(texte_propre, texte, donnees, modele)

        print("[Analyzer] Mode heuristique (Ollama absent)")
        return self._heuristique(texte, donnees)

    def fusionner(self, invitation: MeetingData, contenu: MeetingData) -> MeetingData:

        def dedup(a: list, b: list) -> list:
            vus, res = set(), []
            for item in a + b:
                if isinstance(item, str) and item not in vus:
                    res.append(item)
                    vus.add(item)
            return res

        return MeetingData(
            titre=invitation.titre or contenu.titre,
            date=invitation.date or contenu.date,
            lieu=invitation.lieu or contenu.lieu,
            organisateur=invitation.organisateur,
            duree=invitation.duree or contenu.duree,
            ordre_du_jour=invitation.ordre_du_jour or contenu.ordre_du_jour,
            participants=dedup(invitation.participants, contenu.participants),
            resume=contenu.resume,
            points_discutes=contenu.points_discutes,
            decisions=contenu.decisions,
            actions=contenu.actions,
            prochaines_etapes=contenu.prochaines_etapes,
            source_type="hybride",
        )

    # ── Détection modèle

    def _detecter_modele(self) -> Optional[str]:
        if self._modele_cache is not None:
            return None if self._modele_cache == "_ABSENT_" else self._modele_cache
        try:
            import requests

            r = requests.get(
                f"{OLLAMA['base_url']}/api/tags",
                timeout=OLLAMA["timeout_conn"],
            )
            modeles = [m["name"] for m in r.json().get("models", [])]
            print(f"[Analyzer] Modèles disponibles : {modeles}")

            for pref in OLLAMA["modeles_preferes"]:
                if pref in modeles:
                    print(f"[Analyzer] Modèle sélectionné : {pref}")
                    self._modele_cache = pref
                    return pref

            for pref in OLLAMA["modeles_preferes"]:
                for m in modeles:
                    if m.startswith(pref.split(":")[0]):
                        print(f"[Analyzer] Modèle sélectionné : {m}")
                        self._modele_cache = m
                        return m

            if modeles:
                self._modele_cache = modeles[0]
                return modeles[0]

        except Exception as e:
            print(f"[Analyzer] Ollama connexion échouée : {e}")

        self._modele_cache = "_ABSENT_"
        return None

    # ── Appel Ollama streaming

    def _appel_ollama(self, prompt: str, modele: str) -> str:
        try:
            r = requests.post(
                f"{OLLAMA['base_url']}/api/generate",
                json={
                    "model": modele,
                    "prompt": prompt,
                    "think": False,
                    "stream": True,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": OLLAMA["num_predict"],
                        "num_ctx": 2048,
                    },
                },
                timeout=OLLAMA["timeout_gen"],
                stream=True,
            )
            r.raise_for_status()
            brut = ""
            for ligne in r.iter_lines():
                if ligne:
                    try:
                        chunk = json.loads(ligne)
                        brut += chunk.get("response", "")
                        if chunk.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue
            return brut.strip()
        except Exception as e:
            print(f"[Analyzer] Appel Ollama échoué : {e}")
            return ""

    # ── Stratégie principale : prompt Markdown ──────────────

    def _avec_ollama(
        self,
        texte_propre: str,
        texte_original: str,
        donnees: MeetingData,
        modele: str,
    ) -> MeetingData:
        """
        Stratégie optimale pour llama3.2:1b :
        - Prompt qui demande du Markdown structuré avec sections fixes
        - Le modèle produit naturellement ce format
        - Parser Markdown robuste extrait les données
        """
        extrait = texte_propre[:1400] + (
            "\n[...tronqué...]" if len(texte_propre) > 1400 else ""
        )

        prompt = (
            "Tu es un assistant spécialisé en rédaction de comptes rendus professionnels.\n"
            "Analyse cette transcription/notes de réunion et rédige un compte rendu structuré.\n"
            "Utilise UNIQUEMENT les informations présentes dans le texte. N'invente rien.\n\n"
            "=== TEXTE ===\n"
            f"{extrait}\n"
            "=== FIN ===\n\n"
            "Rédige le compte rendu avec EXACTEMENT ces sections dans cet ordre :\n\n"
            "**TITRE:** [titre décrivant le sujet réel]\n\n"
            "**PARTICIPANTS:** [noms des personnes mentionnées]\n\n"
            "**RESUME:** [2-3 phrases résumant fidèlement ce qui a été discuté]\n\n"
            "**POINTS DISCUTES:**\n"
            "- [point 1 réellement abordé]\n"
            "- [point 2 réellement abordé]\n\n"
            "**DECISIONS:**\n"
            "- [décision réellement prise]\n\n"
            "**ACTIONS:**\n"
            "- [responsable] : [action concrète] | [échéance si mentionnée]\n\n"
            "**PROCHAINES ETAPES:**\n"
            "- [étape mentionnée]\n\n"
            "Si une section est vide, écris : (aucun)\n"
            "Réponds uniquement avec le compte rendu, sans commentaire."
        )

        print("[Analyzer] Appel Ollama (prompt Markdown)...")
        brut = self._appel_ollama(prompt, modele)
        print(f"[DEBUG] Réponse Ollama ({len(brut)} chars):\n{brut}\n")

        if not brut.strip():
            print("[Analyzer] Réponse vide → heuristique")
            return self._heuristique(texte_original, donnees)

        # Parse le Markdown structuré
        donnees = self._parser_markdown(brut, donnees)
        donnees = self._filtrer(donnees)

        # Vérifie qu'on a du contenu utile
        if not donnees.resume and not donnees.points_discutes and not donnees.actions:
            print("[Analyzer] Résultat vide → heuristique")
            return self._heuristique(texte_original, donnees)

        print(
            f"[Analyzer] Résultat — "
            f"titre: '{donnees.titre}' | "
            f"{len(donnees.points_discutes)} points | "
            f"{len(donnees.decisions)} décisions | "
            f"{len(donnees.actions)} actions"
        )
        return donnees

    # ── Parser Markdown structuré

    def _parser_markdown(self, brut: str, donnees: MeetingData) -> MeetingData:
        """
        Parse la réponse Markdown du modèle.
        Cherche les sections **NOM:** et extrait leur contenu.
        """

        def section(texte: str, *labels) -> str:
            """Extrait le contenu d'une section **LABEL:**"""
            for label in labels:
                pattern = (
                    rf"\*{{1,2}}{label}\*{{0,2}}\s*:?\*{{0,2}}\s*(.*?)"
                    rf"(?=\n\*{{1,2}}[A-ZÉÀÈÊ]|\Z)"
                )
                m = re.search(pattern, texte, re.IGNORECASE | re.DOTALL)
                if m:
                    return m.group(1).strip()
            return ""

        def liste(texte: str, *labels) -> list:
            """Extrait une liste à puces d'une section."""
            contenu = section(texte, *labels)
            if not contenu:
                return []
            items = []
            for ligne in contenu.splitlines():
                ligne = re.sub(r"^[\s\-\*\d\.\)]+", "", ligne).strip()
                if (
                    ligne
                    and len(ligne) > 4
                    and ligne.lower() not in _PLACEHOLDERS
                    and "(aucun)" not in ligne.lower()
                ):
                    items.append(ligne)
            return items

        def champ(texte: str, *labels) -> str:
            """Extrait un champ sur une ligne."""
            contenu = section(texte, *labels)
            if not contenu:
                return ""
            # Prend la première ligne non vide
            for ligne in contenu.splitlines():
                ligne = ligne.strip()
                if (
                    ligne
                    and len(ligne) > 2
                    and ligne.lower() not in _PLACEHOLDERS
                    and "(aucun)" not in ligne.lower()
                ):
                    return ligne
            return ""

        # ── Extraction champs simples ──
        titre = champ(brut, "TITRE", "Titre", "SUJET", "Sujet")
        if titre:
            donnees.titre = titre

        date_trouvee = champ(brut, "DATE", "Date")
        if date_trouvee:
            donnees.date = date_trouvee
        elif not donnees.date:
            m = _RE_DATE.search(brut)
            donnees.date = m.group(1) if m else datetime.now().strftime("%d/%m/%Y")

        lieu = champ(brut, "LIEU", "Lieu")
        if lieu:
            donnees.lieu = lieu

        orga = champ(brut, "ORGANISATEUR", "Organisateur")
        if orga:
            donnees.organisateur = orga

        # ── Résumé ──
        resume_brut = section(brut, "RESUME", "Résumé", "RÉSUMÉ", "Resume")
        if resume_brut:
            # Prend le texte direct (pas une liste)
            lignes = [
                l.strip()
                for l in resume_brut.splitlines()
                if l.strip() and not l.strip().startswith("-")
            ]
            if lignes:
                donnees.resume = " ".join(lignes[:3])

        # ── Participants ──
        participants_brut = section(brut, "PARTICIPANTS", "Participants")
        if participants_brut:
            parts = []
            for ligne in participants_brut.splitlines():
                ligne = re.sub(r"^[\s\-\*]+", "", ligne).strip()
                if not ligne or "(aucun)" in ligne.lower():
                    continue
                # Peut être "Nom1, Nom2" ou "- Nom1\n- Nom2"
                for p in re.split(r"[,;]", ligne):
                    p = p.strip()
                    if p and len(p) > 1 and len(p.split()) <= 5:
                        parts.append(p)
            if parts:
                donnees.participants = parts or donnees.participants

        # ── Listes ──
        donnees.points_discutes = liste(
            brut,
            "POINTS DISCUTES",
            "Points discutés",
            "POINTS CLÉS",
            "Points clés",
            "POINTS",
            "Points",
        )
        donnees.decisions = liste(
            brut,
            "DECISIONS",
            "Décisions",
            "DÉCISIONS",
            "DÉCISIONS PRISES",
            "Décisions prises",
        )
        donnees.prochaines_etapes = liste(
            brut,
            "PROCHAINES ETAPES",
            "Prochaines étapes",
            "PROCHAINES ÉTAPES",
            "Suite",
            "SUITE",
        )

        # ── Actions (format "responsable : texte, échéance")
        actions_brut = section(brut, "ACTIONS", "Actions", "ACTIONS À MENER")
        if actions_brut:
            donnees.actions = []
            for ligne in actions_brut.splitlines():
                ligne = re.sub(r"^[\s\-\*\d\.\)]+", "", ligne).strip()
                if not ligne or len(ligne) < 6 or "(aucun)" in ligne.lower():
                    continue
                if ligne.lower() in _PLACEHOLDERS:
                    continue

                responsable = "À définir"
                echeance = ""
                priorite = "normale"
                texte_action = ligne

                # Format "Responsable : action | échéance"
                if ":" in ligne:
                    parties = ligne.split(":", 1)
                    candidat_resp = parties[0].strip()
                    # Le responsable est court (prénom ou équipe)
                    if len(candidat_resp.split()) <= 3 and len(candidat_resp) < 30:
                        responsable = candidat_resp
                        texte_action = parties[1].strip()

                # Extrait l'échéance après "|"
                if "|" in texte_action:
                    parties_ech = texte_action.split("|", 1)
                    texte_action = parties_ech[0].strip()
                    echeance = parties_ech[1].strip()

                # Détecte priorité haute
                if re.search(
                    r"\b(urgent|urgente|critique|asap|dès demain|demain|aujourd'hui)\b",
                    ligne,
                    re.IGNORECASE,
                ):
                    priorite = "haute"

                if len(texte_action) > 5:
                    donnees.actions.append(
                        Action(
                            texte=texte_action,
                            responsable=responsable,
                            echeance=echeance,
                            priorite=priorite,
                        )
                    )

        return donnees

    # ── Filtre anti-placeholder

    def _filtrer(self, donnees: MeetingData) -> MeetingData:

        def nettoyer(lst: list) -> list:
            return [
                item
                for item in lst
                if item
                and item.strip().lower() not in _PLACEHOLDERS
                and len(item.strip()) > 4
            ]

        if donnees.titre and donnees.titre.lower() in _PLACEHOLDERS:
            donnees.titre = ""
        if donnees.resume and donnees.resume.lower() in _PLACEHOLDERS:
            donnees.resume = ""

        donnees.points_discutes = nettoyer(donnees.points_discutes)
        donnees.decisions = nettoyer(donnees.decisions)
        donnees.prochaines_etapes = nettoyer(donnees.prochaines_etapes)
        donnees.ordre_du_jour = nettoyer(donnees.ordre_du_jour)

        donnees.actions = [
            a
            for a in donnees.actions
            if a.texte
            and a.texte.strip().lower() not in _PLACEHOLDERS
            and len(a.texte.strip()) > 5
        ]
        return donnees

    # ── Heuristique (fallback sans Ollama)

    def _heuristique(self, texte: str, donnees: MeetingData) -> MeetingData:
        if not donnees.date:
            donnees.date = self._date(texte)
        if not donnees.titre:
            donnees.titre = self._titre(texte)
        if not donnees.lieu:
            donnees.lieu = self._lieu(texte)
        if not donnees.organisateur:
            donnees.organisateur = self._organisateur(texte)
        if not donnees.participants:
            donnees.participants = self._participants(texte)
        if not donnees.ordre_du_jour:
            donnees.ordre_du_jour = self._odj(texte)
        if not donnees.decisions:
            donnees.decisions = self._decisions(texte)
        if not donnees.actions:
            donnees.actions = self._actions_regex(texte)

        if not donnees.resume:
            phrases = self._phrases_substantielles(texte)
            donnees.resume = (
                " ".join(phrases[:2])
                if phrases
                else (
                    "Analyse automatique limitée — Ollama non disponible. "
                    "Installez Ollama et exécutez : ollama pull llama3.2:1b"
                )
            )
        return donnees

    # ── Nettoyage oral

    def _nettoyer_oral(self, texte: str) -> str:
        t = _RE_SYSTEME.sub("", texte)
        t = _RE_LOCUTEUR.sub("", t)
        t = _RE_TIMESTAMP.sub("", t)
        t = _RE_BRUIT.sub("", t)
        lignes = [l.strip() for l in t.splitlines() if len(l.strip()) > 20]
        t = "\n".join(lignes)
        t = re.sub(r"\b(\w+)(\s+\1){2,}\b", r"\1", t, flags=re.IGNORECASE)
        t = re.sub(r"[ \t]{2,}", " ", t)
        t = re.sub(r"\n{3,}", "\n\n", t)
        return t.strip()

    # ── Extracteurs regex

    def _titre(self, texte: str) -> str:
        for p in [
            r"(?:objet|sujet)[:\s]+([^\n]{3,80})",
            r"(?:^|\n)#\s+([^\n]{3,80})",
        ]:
            m = re.search(p, texte, re.IGNORECASE | re.MULTILINE)
            if m:
                return m.group(1).strip()
        return ""

    def _date(self, texte: str) -> str:
        m = _RE_DATE.search(texte)
        return m.group(1) if m else datetime.now().strftime("%d/%m/%Y")

    def _lieu(self, texte: str) -> str:
        m = re.search(
            r"(?:lieu|salle|locaux?)[:\s]+([^\n,]{3,50})",
            texte,
            re.IGNORECASE,
        )
        if m:
            val = m.group(1).strip()
            if len(val.split()) <= 8:
                return val
        return ""

    def _organisateur(self, texte: str) -> str:
        m = re.search(
            r"(?:organisateur|organisé par)[:\s]+([^\n,;]{3,60})",
            texte,
            re.IGNORECASE,
        )
        return m.group(1).strip() if m else ""

    def _participants(self, texte: str) -> list:
        m = re.search(
            r"(?:participants?|présents?|invités?)[:\s]+([^\n]{5,300})",
            texte,
            re.IGNORECASE,
        )
        if m:
            return [
                p.strip()
                for p in re.split(r"[,;/\n]+", m.group(1))
                if p.strip() and 2 < len(p.strip()) <= 50
            ]
        return []

    def _odj(self, texte: str) -> list:
        m = re.search(
            r"(?:ordre du jour|agenda)[:\s]*\n((?:.+\n?){1,10}?)(?:\n\n|\Z)",
            texte,
            re.IGNORECASE,
        )
        if m:
            return [
                re.sub(r"^[\s\-\d\.]+", "", l).strip()
                for l in m.group(1).splitlines()
                if l.strip() and len(l.strip()) > 3
            ]
        return []

    def _decisions(self, texte: str) -> list:
        resultats = []
        for m in re.finditer(
            r"(?:décidé|validé|approuvé|acté|convenu|confirmé"
            r"|il a été décidé|nous allons|on va)[^\n.]{5,200}",
            texte,
            re.IGNORECASE,
        ):
            val = m.group(0).strip()
            if len(val) > 10:
                resultats.append(val[:250])
        return resultats[:5]

    def _actions_regex(self, texte: str) -> list:
        resultats = []
        for m in re.finditer(
            r"([A-ZÀ-Ÿ][a-zA-ZÀ-ÿ]+(?:\s+[A-ZÀ-Ÿ][a-zA-ZÀ-ÿ]+)*)"
            r"\s+(?:doit|devra|va|prendra en charge|sera chargé de)"
            r"[^\n.]{5,200}",
            texte,
            re.IGNORECASE,
        ):
            val = m.group(0).strip()
            resp = m.group(1).strip().split()[0]
            if len(val) > 10:
                resultats.append(Action(texte=val[:250], responsable=resp))
        return resultats[:8]

    def _phrases_substantielles(self, texte: str) -> list:
        phrases = re.split(r"[.!?]\s+", texte)
        return [
            p.strip()
            for p in phrases
            if 40 <= len(p.strip()) <= 300
            and not re.match(r"^(euh|hmm|ok|oui|non)\b", p.strip(), re.IGNORECASE)
        ][:3]
