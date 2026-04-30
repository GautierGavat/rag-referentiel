"""
app.py — Point d'entrée de l'application Sofia.

Responsabilités :
  - Diagnostic de démarrage (vérification des chemins)
  - Lancement du serveur Gradio
"""
import os
import gradio as gr
from config import CURRENT_FILE_PATH, INDEX_DIR
from ui import build_demo

# ── Diagnostic au démarrage ───────────────────────────
print("--- 🚨 DIAGNOSTIC DE SURVIE 🚨 ---")
print(f"Le script s'exécute depuis : {CURRENT_FILE_PATH}")
print(f"L'index est attendu ici    : {INDEX_DIR}")

if os.path.isdir(INDEX_DIR):
    content = os.listdir(INDEX_DIR)
    print(f"✅ Dossier trouvé ! Fichiers présents : {content}")
else:
    print("❌ Dossier INTROUVABLE au chemin spécifié.")
    print(f"   Voisinage du script : {os.listdir(CURRENT_FILE_PATH)}")

# ── Lancement ────────────────────────────────────────
if __name__ == "__main__":
    demo = build_demo()
    port = int(os.environ.get("PORT", 7860))
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        theme=gr.themes.Soft(),
    )