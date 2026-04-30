"""
ui.py — Interface Gradio : CSS, composants, handlers d'événements.
"""
import gradio as gr
from rag import chat_with_sofia

# ── Constante d'indicateur de réflexion ──────────────
THINKING_PLACEHOLDER = "▪▪▪ *Sofia réfléchit...*"

# ── CSS injecté via gr.HTML (fiable dans Gradio 6.x) ─
STYLE_HTML = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

body, .gradio-container, .main {
    font-family: 'Inter', sans-serif !important;
    background: #f0f2f5 !important;
}

/* ── En-tête ── */
.sofia-header {
    background: linear-gradient(135deg, #e2001a 0%, #b00014 100%);
    padding: 32px 24px 28px;
    border-radius: 16px;
    text-align: center;
    margin-bottom: 20px;
    box-shadow: 0 12px 40px rgba(226,0,26,0.28);
}
.sofia-header h1 {
    color: white !important;
    font-size: 2.2rem !important;
    font-weight: 800 !important;
    margin: 0 0 6px 0 !important;
    letter-spacing: -1px;
}
.sofia-header p {
    color: rgba(255,255,255,0.85) !important;
    font-size: 0.95rem !important;
    margin: 0 !important;
}

@media (max-width: 768px) {
    .sofia-header h1 { font-size: 1.6rem !important; }
}
</style>
"""


# ── Handlers ─────────────────────────────────────────

def user_message(message: str, history: list):
    """
    Ajoute le message de l'utilisateur et un placeholder de réflexion
    dans l'historique du chatbot.
    """
    if not message.strip():
        return message, history
    new_history = list(history) if history else []
    new_history.append({"role": "user", "content": message})
    new_history.append({"role": "assistant", "content": THINKING_PLACEHOLDER})
    return "", new_history


def bot_response(history: list):
    """
    Remplace le placeholder par la vraie réponse de Sofia, streamée token par token.
    """
    # Extraire le dernier message utilisateur (contenu peut être str ou list multi-modal)
    user_msg = ""
    for msg in reversed(history):
        if isinstance(msg, dict) and msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, list):
                user_msg = " ".join(
                    c.get("text", str(c)) if isinstance(c, dict) else str(c)
                    for c in content
                )
            else:
                user_msg = str(content).strip()
            break

    # Historique propre : sans le dernier placeholder assistant
    prev_history = [
        m for m in history[:-1]
        if isinstance(m, dict) and m.get("content") != THINKING_PLACEHOLDER
    ]

    new_history = list(history)
    for partial in chat_with_sofia(user_msg, prev_history):
        new_history[-1] = {"role": "assistant", "content": partial}
        yield new_history


# ── Construction de l'interface Gradio ───────────────

def build_demo() -> gr.Blocks:
    """Construit et retourne l'objet gr.Blocks de l'application."""
    with gr.Blocks(title="Sofia — Assistant Pédagogique RNCP") as demo:

        gr.HTML(STYLE_HTML)

        gr.HTML("""
            <div class="sofia-header">
                <h1>🤖 Sofia</h1>
                <p>Assistante Pédagogique RNCP · Simplon</p>
            </div>
        """)

        chatbot = gr.Chatbot(
            label="Chat avec Sofia",
            height=520,
            elem_classes=["chatbot-wrap"],
        )

        with gr.Row():
            msg_input = gr.Textbox(
                placeholder="Décrivez votre projet ou posez une question...",
                show_label=False,
                scale=9,
                container=False,
            )
            send_btn = gr.Button("Envoyer ▶", variant="primary", scale=1)

        gr.ClearButton([msg_input, chatbot], value="🗑  Nouvelle conversation")

        # Envoi via bouton
        send_btn.click(
            fn=user_message,
            inputs=[msg_input, chatbot],
            outputs=[msg_input, chatbot],
        ).then(
            fn=bot_response,
            inputs=[chatbot],
            outputs=[chatbot],
        )

        # Envoi via touche Entrée
        msg_input.submit(
            fn=user_message,
            inputs=[msg_input, chatbot],
            outputs=[msg_input, chatbot],
        ).then(
            fn=bot_response,
            inputs=[chatbot],
            outputs=[chatbot],
        )

    return demo
