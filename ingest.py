"""
ingest.py — Pipeline d'ingestion du référentiel RNCP.

Étapes :
  1. LOAD   → Chargement des PDFs depuis rag/data/
  2. SPLIT  → Découpage en chunks avec chevauchement
  3. EMBED  → Génération des embeddings (MiniLM multilingue)
  4. STORE  → Sauvegarde de l'index FAISS dans rag/index/

Usage :
    python ingest.py

À relancer uniquement si le contenu des PDFs change.
"""
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# ── Chemins ──────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_DIR  = os.path.join(BASE_DIR, "rag", "data")
INDEX_DIR = os.path.join(BASE_DIR, "rag", "index")

# ── Paramètres de chunking ───────────────────────────
CHUNK_SIZE    = 700   # Taille des chunks en caractères
CHUNK_OVERLAP = 150   # Chevauchement pour ne pas couper une compétence

# ── Modèle d'embeddings ──────────────────────────────
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def load_documents(data_dir: str) -> list:
    """
    ÉTAPE 1 — LOAD
    Charge tous les fichiers PDF présents dans data_dir.
    """
    documents = []
    pdf_files = [f for f in os.listdir(data_dir) if f.endswith(".pdf")]

    if not pdf_files:
        raise FileNotFoundError(
            f"❌ Aucun fichier PDF trouvé dans '{data_dir}'.\n"
            "   → Placez le référentiel RNCP (PDF) dans ce dossier avant de relancer."
        )

    for filename in pdf_files:
        path = os.path.join(data_dir, filename)
        print(f"  📄 Chargement : {filename}")
        loader = PyPDFLoader(path)
        documents.extend(loader.load())

    print(f"  ✅ {len(documents)} pages chargées depuis {len(pdf_files)} fichier(s).\n")
    return documents


def split_documents(documents: list) -> list:
    """
    ÉTAPE 2 — SPLIT
    Découpe les documents en chunks avec chevauchement.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    print(f"  ✅ {len(chunks)} chunks créés "
          f"(taille={CHUNK_SIZE}, overlap={CHUNK_OVERLAP}).\n")
    return chunks


def embed_and_store(chunks: list, index_dir: str) -> None:
    """
    ÉTAPES 3 & 4 — EMBED + STORE
    Génère les embeddings et sauvegarde l'index FAISS sur disque.
    """
    print(f"  🔄 Chargement du modèle d'embeddings : {EMBEDDING_MODEL}")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    print(f"  🔄 Génération des embeddings et construction de l'index FAISS...")
    vector_store = FAISS.from_documents(chunks, embeddings)

    os.makedirs(index_dir, exist_ok=True)
    vector_store.save_local(index_dir)
    print(f"  ✅ Index FAISS sauvegardé dans '{index_dir}'.\n")


def main():
    print("=" * 55)
    print("  🚀 INGESTION DU RÉFÉRENTIEL RNCP — Sofia RAG")
    print("=" * 55)

    # Étape 1 — Load
    print("\n[1/4] LOAD — Chargement des PDFs...")
    documents = load_documents(DATA_DIR)

    # Étape 2 — Split
    print("[2/4] SPLIT — Découpage en chunks...")
    chunks = split_documents(documents)

    # Étapes 3 & 4 — Embed + Store
    print("[3/4] EMBED — Génération des embeddings...")
    print("[4/4] STORE — Sauvegarde de l'index FAISS...")
    embed_and_store(chunks, INDEX_DIR)

    print("=" * 55)
    print("  ✅ Ingestion terminée ! Vous pouvez lancer : python app.py")
    print("=" * 55)


if __name__ == "__main__":
    main()
