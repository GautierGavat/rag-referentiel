"""
config.py — Configuration globale : chemins, constantes, modèles LLM et embeddings.
"""
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

# ── Chemins ──────────────────────────────────────────
CURRENT_FILE_PATH = os.path.dirname(os.path.abspath(__file__))
INDEX_DIR = os.path.join(CURRENT_FILE_PATH, "rag", "index")

# ── Paramètres RAG ───────────────────────────────────
SCORE_THRESHOLD = 15.0  # Distance FAISS L2 max (0 = parfait, >15 = hors-sujet)
K_RESULTS = 6           # Nombre de chunks récupérés

# ── Modèle d'embeddings (local, multilingue) ─────────
embeddings_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

# ── LLM Gemini ───────────────────────────────────────
def get_gemini_llm():
    """Instancie le LLM Gemini si la clé API est disponible."""
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ ERREUR : Aucune clé API Gemini trouvée (GOOGLE_API_KEY / GEMINI_API_KEY) !")
        return None
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=api_key,
        temperature=0,
        streaming=True,
    )

llm = get_gemini_llm()
