"""
rag.py — Chargement du vector store FAISS et logique de chat RAG.
"""
import os
from langchain_community.vectorstores import FAISS
from config import INDEX_DIR, embeddings_model, llm, SCORE_THRESHOLD, K_RESULTS


def load_vector_store():
    """Charge l'index FAISS depuis le disque. Retourne None si introuvable."""
    faiss_index_path = os.path.join(INDEX_DIR, "index.faiss")
    if os.path.exists(faiss_index_path):
        try:
            vs = FAISS.load_local(
                INDEX_DIR,
                embeddings_model,
                allow_dangerous_deserialization=True,
            )
            print("✅ SUCCÈS : FAISS chargé avec succès.")
            return vs
        except Exception as e:
            print(f"❌ ERREUR CHARGEMENT FAISS : {e}")
    return None


# Singleton chargé au démarrage
vector_store = load_vector_store()


def chat_with_sofia(message, history: list):
    """
    Générateur RAG + LLM streamé.

    Args:
        message : message courant (str ou list multi-modal Gradio 6.x)
        history : liste de dicts {"role", "content"} déjà filtrée (sans placeholders)

    Yields:
        str — réponse partielle accumulée
    """
    # Normalisation du message (Gradio 6.x peut envoyer une liste multi-modale)
    if isinstance(message, list):
        message = " ".join(
            item.get("text", str(item)) if isinstance(item, dict) else str(item)
            for item in message
        )
    message = str(message).strip()

    if not message:
        yield "⚠️ Veuillez saisir un message."
        return

    if not vector_store:
        yield "❌ Erreur : L'index documentaire n'est pas chargé."
        return

    # ── Recherche sémantique ──────────────────────────
    results = vector_store.similarity_search_with_score(message, k=K_RESULTS)
    filtered_results = [doc for doc, score in results if score <= SCORE_THRESHOLD]

    context = ""
    if filtered_results:
        context = "\n\n".join([f"Extrait :\n{doc.page_content}" for doc in filtered_results])

    # ── Construction du contexte historique ──────────
    history_text = ""
    for msg in history[-8:]:  # 4 derniers échanges (user + assistant)
        if isinstance(msg, dict):
            role = "Utilisateur" if msg.get("role") == "user" else "Sofia"
            content = msg.get("content", "")
            if content:
                history_text += f"{role} : {content}\n"

    context_section = f"\nCONTEXTE RÉFÉRENTIEL RNCP :\n{context}\n" if context else ""
    history_section = f"\nHISTORIQUE :\n{history_text}" if history_text else ""

    # ── Prompt ───────────────────────────────────────
    prompt = f"""Tu es Sofia, assistante pédagogique experte chez Simplon, spécialisée dans le référentiel RNCP du titre "Développeur en Intelligence Artificielle".
{context_section}{history_section}
MESSAGE DE L'APPRENANT :
{message}

---

Analyse le projet décrit ci-dessus en t'appuyant UNIQUEMENT sur les extraits du référentiel fournis.
Réponds en français, de façon structurée, selon le format suivant :

## ✅ Compétences couvertes

Pour chaque compétence identifiée, indique :
- Le **code** (ex : C7, C8, C13...)
- L'**intitulé** de la compétence selon le référentiel
- Une **justification** expliquant pourquoi le projet la couvre
- L'**extrait du référentiel** qui le confirme (citation directe)

## ❌ Compétences non couvertes ou partiellement couvertes

Liste les compétences du référentiel qui ne semblent PAS couvertes par le projet décrit, avec une brève explication de ce qui manque.

## 📊 Synthèse

Donne une appréciation globale : le projet est-il solide pour la validation du titre ? Quels sont les points forts et les axes d'amélioration prioritaires ?

⚠️ Ne mentionne que les compétences présentes dans les extraits fournis. N'invente pas de compétences absentes du référentiel."""

    # ── Streaming LLM ─────────────────────────────────
    try:
        partial = ""
        for chunk in llm.stream(prompt):
            if chunk.content:
                partial += chunk.content
                yield partial
    except Exception as e:
        yield f"⚠️ Erreur LLM : {str(e)}"
