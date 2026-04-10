import gradio as gr
from src.core.agents.orchestrator import Orchestrator
from src.config import UI, FORMAT_MAP

orch = Orchestrator()


def generer(
    inv_texte,
    inv_fichier,
    cont_texte,
    cont_fichier_texte,
    cont_fichier_audio,
    type_sortie,
    langue,
) -> tuple:

    if cont_fichier_audio:
        fichier_contenu, texte_contenu = cont_fichier_audio, None
    elif cont_fichier_texte:
        fichier_contenu, texte_contenu = cont_fichier_texte, None
    else:
        fichier_contenu, texte_contenu = None, cont_texte or None

    texte_inv = inv_texte or None
    fichier_inv = inv_fichier or None

    if not any([texte_inv, fichier_inv, texte_contenu, fichier_contenu]):
        return "", None, "Veuillez fournir au moins une entrée."

    formats = FORMAT_MAP.get(type_sortie, FORMAT_MAP["Tous"])

    try:
        r = orch.run_cr(
            texte_invitation=texte_inv,
            fichier_invitation=fichier_inv,
            texte_contenu=texte_contenu,
            fichier_contenu=fichier_contenu,
            langue=langue,
            formats=formats,
        )
        d = r["donnees"]
        fichier_out = (
            r["fichiers"].get("pdf")
            or r["fichiers"].get("word")
            or r["fichiers"].get("txt")
        )
        statut = (
            f"{d.titre or 'Compte rendu généré'} — "
            f"{len(d.actions)} action(s)  ·  "
            f"{len(d.decisions)} décision(s)"
        )
        return r["markdown"], fichier_out, statut

    except Exception as e:
        return "", None, f"Erreur : {e}"


CSS = """
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700;800&family=Inter:wght@400;500&display=swap');

:root {
    --red:    #E8312A;
    --green:  #7AB648;
    --blue:   #1B75BB;
    --pink:   #C0398B;
    --dark:   #1C2130;
    --grey:   #F5F6F8;
    --border: #E3E7EF;
    --text:   #1C2130;
    --muted:  #8492A6;
    --white:  #ffffff;
}

*, *::before, *::after { box-sizing: border-box; }

body, .gradio-container {
    background: var(--grey) !important;
    font-family: 'Inter', sans-serif !important;
    color: var(--text) !important;
}

/* ════════════════════════════
   HEADER 
   ════════════════════════════ */
.ms-header {
    background: var(--dark);
    border-radius: 12px;
    height: 160px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 10px;
    position: relative;
    overflow: hidden;
}
.ms-header::before {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg,
        var(--red) 0%,
        var(--pink) 33%,
        var(--blue) 66%,
        var(--green) 100%);
}
.ms-title {
    font-family: 'Montserrat', sans-serif;
    font-weight: 800;
    font-size: 3rem;
    color: var(--white);
    letter-spacing: -1px;
    line-height: 1;
}
.ms-title span { color: var(--green); }
.ms-sub {
    font-size: 10px;
    color: rgba(255,255,255,0.35);
    letter-spacing: 2.5px;
    text-transform: uppercase;
    font-weight: 600;
    margin-left: 14px;
    align-self: flex-end;
    padding-bottom: 3px;
}

.ms-card {
    background: var(--white);
    border-radius: 10px;
    border: 1px solid var(--border);
    padding: 14px 18px;
    margin-bottom: 10px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.ms-card-head {
    display: flex;
    align-items: center;
    gap: 9px;
    margin-bottom: 12px;
    padding-bottom: 9px;
    border-bottom: 1px solid var(--border);
}

.ms-num {
    width: 24px; height: 24px;
    border-radius: 6px;
    font-family: 'Montserrat', sans-serif;
    font-weight: 800;
    font-size: 12px;
    color: var(--white);
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
}
.n1 { background: var(--red); }
.n2 { background: var(--green); }
.n3 { background: var(--blue); }
.n4 { background: var(--pink); }

/* Bordure gauche colorée sur chaque card */
.ms-card.card-1 { border-left: 4px solid var(--red); }
.ms-card.card-2 { border-left: 4px solid var(--green); }
.ms-card.card-3 { border-left: 4px solid var(--blue); }
.ms-card.card-4 { border-left: 4px solid var(--pink); }

.ms-card-title {
    font-family: 'Montserrat', sans-serif;
    font-weight: 700;
    font-size: 13px;
    color: var(--text);
}
.ms-card-hint {
    font-size: 11px;
    color: var(--muted);
    margin-left: 4px;
}

/* ── Inputs  ── */
.gradio-container label span {
    font-family: 'Montserrat', sans-serif !important;
    font-weight: 600 !important;
    font-size: 10px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.7px !important;
    color: var(--muted) !important;
}
.gradio-container textarea,
.gradio-container input[type="text"] {
    border: 1.5px solid var(--border) !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    background: #FAFBFC !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
.gradio-container textarea:focus,
.gradio-container input[type="text"]:focus {
    border-color: var(--blue) !important;
    box-shadow: 0 0 0 3px rgba(27,117,187,0.10) !important;
}

/* ── Tabs ── */
.gradio-container .tab-nav button {
    font-family: 'Montserrat', sans-serif !important;
    font-weight: 600 !important;
    font-size: 12px !important;
    padding: 6px 12px !important;
}
.gradio-container .tab-nav button.selected {
    color: var(--blue) !important;
    border-bottom: 2px solid var(--blue) !important;
}

/* ── Bouton principal ── */
.gradio-container button.primary {
    background: var(--dark) !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Montserrat', sans-serif !important;
    font-weight: 700 !important;
    font-size: 14px !important;
    letter-spacing: 0.3px !important;
    box-shadow: 0 3px 10px rgba(0,0,0,0.18) !important;
    transition: all 0.2s !important;
}
.gradio-container button.primary:hover {
    background: var(--blue) !important;
    box-shadow: 0 5px 16px rgba(27,117,187,0.35) !important;
    transform: translateY(-1px) !important;
}

/* ── Disclaimer IA  ── */
.ms-disclaimer {
    display: flex;
    align-items: flex-start;
    gap: 9px;
    background: #FFF8E1;
    border: 1px solid #FFD54F;
    border-left: 4px solid #F5A623;
    border-radius: 8px;
    padding: 9px 14px;
    margin-bottom: 12px;
    font-family: 'Inter', sans-serif;
    font-size: 12px;
    color: #5D4037;
    line-height: 1.5;
}
.ms-disclaimer-icon { font-size: 16px; flex-shrink: 0; margin-top: 1px; }
.ms-disclaimer strong { color: #3E2723; font-weight: 700; }

/* ── Résultat Markdown ── */
.gradio-container .prose h1 {
    font-family: 'Montserrat', sans-serif !important;
    font-weight: 800 !important;
    color: var(--dark) !important;
    font-size: 1.1rem !important;
    border-left: 4px solid var(--red) !important;
    padding-left: 10px !important;
    margin-top: 12px !important;
}
.gradio-container .prose h2 {
    font-family: 'Montserrat', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.78rem !important;
    text-transform: uppercase !important;
    letter-spacing: 1.2px !important;
    color: var(--blue) !important;
    margin-top: 14px !important;
}
.gradio-container .prose table { width: 100% !important; font-size: 12px !important; }
.gradio-container .prose th {
    background: var(--dark) !important;
    color: var(--white) !important;
    font-family: 'Montserrat', sans-serif !important;
    font-weight: 700 !important;
    font-size: 10px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.8px !important;
    padding: 7px 10px !important;
}
.gradio-container .prose td {
    padding: 7px 10px !important;
    border-bottom: 1px solid var(--border) !important;
    vertical-align: top !important;
}
.gradio-container .prose tr:nth-child(even) td { background: var(--grey) !important; }

/* ── Footer ── */
.ms-footer {
    text-align: center;
    padding: 10px 0 4px;
    font-size: 11px;
    color: var(--muted);
}
.ms-footer strong {
    font-family: 'Montserrat', sans-serif;
    font-weight: 800;
    letter-spacing: 1px;
    color: var(--dark);
}
.ms-dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    display: inline-block;
    margin: 0 2px;
}
"""

HEADER = """
<div class="ms-header">
    <div class="ms-title">Meet<span>Scribe</span></div>
    <div class="ms-sub">Compte rendu automatique</div>
</div>
"""

DISCLAIMER = """
<div class="ms-disclaimer">
    <span class="ms-disclaimer-icon">🤖</span>
    <span>Ce compte rendu est <strong>généré par l'IA </strong>.
    Il est recommandé de le <strong>relire et valider</strong> avant toute diffusion —
    des erreurs peuvent survenir.</span>
</div>
"""

FOOTER = """
<div class="ms-footer">
    <span class="ms-dot" style="background:#E8312A"></span>
    <span class="ms-dot" style="background:#7AB648"></span>
    <span class="ms-dot" style="background:#1B75BB"></span>
    <span class="ms-dot" style="background:#C0398B"></span>
    &nbsp;&nbsp;<strong>TALAN</strong>&nbsp;&nbsp;·&nbsp;&nbsp;Positive Innovation
</div>
"""


def construire_interface() -> gr.Blocks:
    with gr.Blocks(title="MeetScribe") as demo:
        gr.HTML(HEADER)

        # ── 1 Invitation
        gr.HTML("""<div class="ms-card card-1"><div class="ms-card-head">
            <div class="ms-num n1">1</div>
            <div class="ms-card-title">Invitation de réunion:</div>
            <div class="ms-card-hint">titre , date , lieu , participants , ordre du jour</div>
        </div>""")
        with gr.Row(equal_height=True):
            inv_texte = gr.Textbox(
                label="Coller le texte",
                placeholder="Objet : ...\nDate : ...\nParticipants : ...",
                lines=4,
                scale=1,
            )
            inv_fichier = gr.File(
                label="Ou importer un fichier",
                file_types=[".txt", ".md", ".pdf", ".docx"],
                scale=1,
            )
        gr.HTML("</div>")

        # ── 2 Contenu
        gr.HTML("""<div class="ms-card card-2"><div class="ms-card-head">
            <div class="ms-num n2">2</div>
            <div class="ms-card-title">Contenu de la réunion:</div>
            <div class="ms-card-hint">notes , transcription , audio</div>
        </div>""")
        with gr.Tabs():
            with gr.Tab("Texte / Notes"):
                with gr.Row(equal_height=True):
                    cont_texte = gr.Textbox(
                        label="Coller le texte",
                        placeholder="Notes ou transcription...",
                        lines=4,
                        scale=1,
                    )
                    cont_fichier_texte = gr.File(
                        label="Ou importer un fichier",
                        file_types=[".txt", ".md", ".pdf", ".docx"],
                        scale=1,
                    )
            with gr.Tab(" Audio"):
                cont_fichier_audio = gr.File(
                    label="Fichier audio",
                    file_types=[".mp3", ".wav", ".m4a", ".ogg", ".flac"],
                )
                gr.Markdown("*Transcription locale*")
        gr.HTML("</div>")

        # ── 3 Options
        gr.HTML("""<div class="ms-card card-3"><div class="ms-card-head">
            <div class="ms-num n3">3</div>
            <div class="ms-card-title">Export</div>
        </div>""")
        with gr.Row():
            type_sortie = gr.Radio(
                choices=UI["formats"],
                value="PDF",
                label="Format",
            )
            langue = gr.Dropdown(
                choices=UI["langues"],
                value="fr",
                label="Langue",
            )
        gr.HTML("</div>")

        btn = gr.Button("Générer le compte rendu", variant="primary", size="lg")

        # ── 4 Résultat
        gr.HTML("""<div class="ms-card card-4"><div class="ms-card-head">
            <div class="ms-num n4">4</div>
            <div class="ms-card-title">Résultat</div>
        </div>""")
        gr.HTML(DISCLAIMER)
        statut_out = gr.Textbox(label="Statut", interactive=False, lines=1)
        cr_out = gr.Markdown()
        fichier_out = gr.File(label="Télécharger")
        gr.HTML("</div>")

        gr.HTML(FOOTER)

        btn.click(
            fn=generer,
            inputs=[
                inv_texte,
                inv_fichier,
                cont_texte,
                cont_fichier_texte,
                cont_fichier_audio,
                type_sortie,
                langue,
            ],
            outputs=[cr_out, fichier_out, statut_out],
        )

    return demo


if __name__ == "__main__":
    print(f"\n{'=' * 42}")
    print(f"  MeetScribe → http://localhost:{UI['port']}")
    print(f"{'=' * 42}\n")

    construire_interface().launch(
        server_name=UI["host"],
        server_port=UI["port"],
        show_error=True,
        css=CSS,
    )
