# 🏗️ Architecture — Sofia RAG Assistant

Ce document décrit l'architecture technique complète du projet Sofia.

## Vue d'ensemble

Sofia est un chatbot pédagogique basé sur un pipeline **RAG (Retrieval-Augmented Generation)**. Il permet aux apprenants et formateurs Simplon d'évaluer la couverture de projets par rapport au référentiel RNCP "Développeur en Intelligence Artificielle".

---

## Structure du projet

```
simplon-rag-referentiel/
├── app.py              # Point d'entrée : diagnostic + lancement Gradio
├── config.py           # Configuration globale (chemins, LLM, embeddings)
├── rag.py              # Logique RAG : chargement FAISS + chat_with_sofia()
├── ui.py               # Interface Gradio : CSS, composants, event handlers
│
├── requirements.txt    # Dépendances Python
├── Dockerfile          # Image de production
├── docker-compose.yml  # Orchestration locale (app + Ollama)
├── .env                # Variables d'environnement (non versionné)
├── .env.example        # Template à committer
├── README.md
├── ARCHITECTURE.md     # Ce fichier
│
└── rag/
    ├── data/           # PDF du référentiel RNCP (à placer manuellement)
    └── index/          # Index FAISS généré (index.faiss + index.pkl)
```

---

## Responsabilités des modules

### `app.py` — Point d'entrée

Rôle unique : **démarrer l'application**.

- Affiche un diagnostic de survie au lancement (vérification des chemins)
- Instancie l'interface via `build_demo()` (depuis `ui.py`)
- Lance le serveur Gradio sur `0.0.0.0:PORT`

```python
# Exemple simplifié
from ui import build_demo
demo = build_demo()
demo.launch(server_name="0.0.0.0", server_port=7860)
```

---

### `config.py` — Configuration globale

Centralise tous les paramètres partagés entre les modules.

| Constante | Valeur | Description |
|---|---|---|
| `CURRENT_FILE_PATH` | auto | Répertoire du script |
| `INDEX_DIR` | `rag/index/` | Chemin de l'index FAISS |
| `SCORE_THRESHOLD` | `80.0` | Distance FAISS max (filtre la pertinence) |
| `K_RESULTS` | `8` | Nombre de chunks récupérés par requête |
| `embeddings_model` | MiniLM-L12-v2 | Modèle d'embeddings HuggingFace |
| `llm` | Gemini 2.5 Flash | LLM de génération via Google AI |

---

### `rag.py` — Logique RAG

Contient le cœur fonctionnel du système.

#### `load_vector_store()`
Charge l'index FAISS préalablement construit depuis `rag/index/`. Retourne `None` si l'index est absent.

> ⚠️ L'index doit être construit **avant** le démarrage de l'application. Il n'est pas régénéré automatiquement à chaque lancement.

#### `chat_with_sofia(message, history)`

Pipeline RAG complet, exécuté à chaque message :

```
Message utilisateur
       │
       ▼
1. Normalisation  →  Gestion du format multi-modal Gradio 6.x
       │
       ▼
2. Recherche      →  FAISS similarity_search_with_score (k=8, score ≤ 80)
       │
       ▼
3. Contexte       →  Concaténation des chunks filtrés
       │
       ▼
4. Prompt         →  Injection contexte RNCP + historique (4 derniers échanges)
       │
       ▼
5. LLM Stream     →  Gemini 2.5 Flash (streaming token par token)
       │
       ▼
Réponse streamée → ui.py
```

---

### `ui.py` — Interface Gradio

Gère tout ce qui est visible par l'utilisateur.

#### `STYLE_HTML`
CSS injecté via `gr.HTML()` — contournement fiable des limitations de Gradio 6.x qui ignore le paramètre `css=` passé aux constructeurs.

#### `THINKING_PLACEHOLDER`
Texte affiché dans la bulle de réponse pendant le traitement : `▪▪▪ *Sofia réfléchit...*`

#### `user_message(message, history)`
Vide l'input et ajoute immédiatement le message + placeholder dans le chatbot (feedback visuel instantané).

#### `bot_response(history)`
Remplace le placeholder par la vraie réponse streamée de `chat_with_sofia()`.

#### `build_demo() → gr.Blocks`
Factory qui construit et retourne l'objet Gradio complet. Découplé du `launch()` pour faciliter les tests.

---

## Pipeline RAG — Flux de données

```
┌─────────────────────────────────────────────────────────┐
│                      INDEXATION (offline)               │
│                                                         │
│  PDF référentiel RNCP                                   │
│       ↓ PyPDFLoader                                     │
│  Chunks (size=700, overlap=150)                         │
│       ↓ MiniLM-L12-v2 (HuggingFace)                    │
│  Vecteurs → FAISS index (rag/index/)                    │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                    INFÉRENCE (runtime)                  │
│                                                         │
│  Message utilisateur                                    │
│       ↓ MiniLM-L12-v2 (même modèle)                    │
│  Vecteur requête → FAISS search (k=8, score ≤ 80)      │
│       ↓                                                 │
│  Chunks pertinents + Historique (4 échanges)            │
│       ↓ Prompt engineering                              │
│  Gemini 2.5 Flash (streaming)                           │
│       ↓                                                 │
│  Réponse affichée token par token dans Gradio           │
└─────────────────────────────────────────────────────────┘
```

---

## Stack technique

| Couche | Technologie | Version/Détail |
|---|---|---|
| **Interface** | Gradio | 6.x — `gr.Blocks` + `gr.Chatbot` |
| **LLM** | Google Gemini | `gemini-2.5-flash` via `langchain-google-genai` |
| **Embeddings** | HuggingFace | `paraphrase-multilingual-MiniLM-L12-v2` |
| **Vector Store** | FAISS | CPU, index local sur disque |
| **Orchestration** | LangChain | `langchain-community`, `langchain-huggingface` |
| **PDF Parsing** | PyPDF | Via `langchain-text-splitters` |
| **Config** | python-dotenv | Variables d'environnement via `.env` |
| **Déploiement** | Docker + GCP Cloud Run | Image `python:3.11-slim`, port 7860 |

---

## Déploiement GCP Cloud Run

```
docker build -t gcr.io/<PROJECT_ID>/sofia-rag:latest .
docker push gcr.io/<PROJECT_ID>/sofia-rag:latest
gcloud run deploy sofia-rag \
  --image gcr.io/<PROJECT_ID>/sofia-rag:latest \
  --region europe-west1 \
  --platform managed
```

> La variable `GEMINI_API_KEY` doit être configurée dans les secrets Cloud Run, **pas** dans le `.env` qui n'est pas versionné.

---

## Variables d'environnement

| Variable | Obligatoire | Description |
|---|---|---|
| `GOOGLE_API_KEY` | Oui* | Clé API Google AI Studio |
| `GEMINI_API_KEY` | Oui* | Alias accepté pour la clé Gemini |
| `PORT` | Non | Port du serveur (défaut : `7860`) |

*L'une ou l'autre suffit. `GOOGLE_API_KEY` est prioritaire.
