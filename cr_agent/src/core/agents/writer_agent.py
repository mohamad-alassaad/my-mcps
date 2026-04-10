from datetime import datetime
from src.core.agents.analyzer_agent import MeetingData


class WriterAgent:
    def rediger(self, d: MeetingData) -> str:
        sections = [
            self._entete(d),
            self._ordre_du_jour(d),
            self._resume(d),
            self._points_discutes(d),
            self._decisions(d),
            self._actions(d),
            self._prochaines_etapes(d),
            self._pied(),
        ]
        return "\n\n".join(s for s in sections if s.strip())

    def _entete(self, d: MeetingData) -> str:
        lignes = [f"# {d.titre or 'Compte rendu de réunion'}", ""]
        for label, valeur in [
            ("Date", d.date),
            ("Lieu", d.lieu),
            ("Organisateur", d.organisateur),
            ("Durée", d.duree),
            ("Participants", ", ".join(d.participants) if d.participants else ""),
        ]:
            if valeur:
                lignes.append(f"- **{label}** : {valeur}")
        return "\n".join(lignes)

    def _ordre_du_jour(self, d: MeetingData) -> str:
        if not d.ordre_du_jour:
            return ""
        items = "\n".join(f"{i}. {p}" for i, p in enumerate(d.ordre_du_jour, 1))
        return f"## Ordre du jour\n\n{items}"

    def _resume(self, d: MeetingData) -> str:
        return f"## Résumé\n\n{d.resume}" if d.resume else ""

    def _points_discutes(self, d: MeetingData) -> str:
        if not d.points_discutes:
            return ""
        items = "\n".join(f"- {p}" for p in d.points_discutes)
        return f"## Points discutés\n\n{items}"

    def _decisions(self, d: MeetingData) -> str:
        if not d.decisions:
            return ""
        items = "\n".join(f"- {dec}" for dec in d.decisions)
        return f"## Décisions prises\n\n{items}"

    def _actions(self, d: MeetingData) -> str:
        if not d.actions:
            return ""
        lignes = [
            "## Actions à mener",
            "",
            "| # | Action | Responsable | Échéance | Priorité |",
            "|---|--------|-------------|----------|----------|",
        ]
        for i, a in enumerate(d.actions, 1):
            lignes.append(
                f"| {i} | {a.texte} | {a.responsable} "
                f"| {a.echeance or '—'} | {a.priorite.upper()} |"
            )
        return "\n".join(lignes)

    def _prochaines_etapes(self, d: MeetingData) -> str:
        if not d.prochaines_etapes:
            return ""
        items = "\n".join(f"{i}. {e}" for i, e in enumerate(d.prochaines_etapes, 1))
        return f"## Prochaines étapes\n\n{items}"

    def _pied(self) -> str:
        return f"---\n*Généré par MeetScribe le {datetime.now().strftime('%d/%m/%Y à %H:%M')}*"
