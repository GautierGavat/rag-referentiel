# 🎓 Sofia — Assistant RAG · Référentiel RNCP Dev IA (Simplon)

Chatbot pédagogique basé sur un pipeline **RAG (Retrieval-Augmented Generation)** permettant aux apprenants et formateurs Simplon d'évaluer la couverture d'un projet par rapport au référentiel RNCP "Développeur en Intelligence Artificielle".

---

## ✨ Fonctionnalités

- 💬 **Chat conversationnel** multi-tours avec mémoire des 4 derniers échanges
- 🔍 **Recherche sémantique** dans le référentiel RNCP via FAISS
- ⚡ **Streaming** — la réponse s'affiche token par token
- 🎨 **Interface responsive** aux couleurs Simplon (rouge `#e2001a`, police Inter)
- ☁️ **Déployé sur GCP Cloud Run**

---

## 🏗️ Architecture

Le projet est découpé en **4 modules** selon le principe de séparation des responsabilités :

```
simplon-rag-referentiel/
├── app.py              # Point d'entrée : diagnostic + lancement Gradio
├── config.py           # Configuration globale (chemins, LLM, embeddings)
├── rag.py              # Logique RAG : FAISS + chat_with_sofia()
├── ui.py               # Interface Gradio : CSS, composants, event handlers
│
├── requirements.txt    # Dépendances Python
├── Dockerfile          # Image de production
├── docker-compose.yml  # Orchestration locale
├── .env.example        # Template de variables d'environnement
├── ARCHITECTURE.md     # Documentation technique détaillée
│
└── rag/
    ├── data/           # PDF du référentiel RNCP (à placer ici)
    └── index/          # Index FAISS (index.faiss + index.pkl)
```

> 📖 Pour une description détaillée de chaque module, voir [ARCHITECTURE.md](./ARCHITECTURE.md).

---

## 🤖 Stack technique

| Couche | Technologie |
|---|---|
| Interface | Gradio 6.x (`gr.Blocks` + `gr.Chatbot`) |
| LLM | **Google Gemini 2.5 Flash** via `langchain-google-genai` |
| Embeddings | `paraphrase-multilingual-MiniLM-L12-v2` (HuggingFace, 100% local) |
| Vector Store | **FAISS** (CPU, index sur disque) |
| Orchestration | LangChain Community |
| Déploiement | Docker + **GCP Cloud Run** (`europe-west1`) |

---

## 🚀 Lancement local

### Prérequis

- Python 3.11+
- Une clé API [Google AI Studio](https://aistudio.google.com/) (gratuite)

### Installation

```bash
# 1. Cloner le dépôt
git clone <url-du-repo>
cd simplon-rag-referentiel

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Configurer les variables d'environnement
cp .env.example .env
# → Renseigner GEMINI_API_KEY dans le fichier .env

# 4. Placer le PDF du référentiel RNCP dans :
#    rag/data/

# 5. Lancer l'application
python app.py
```

L'interface est accessible sur **http://localhost:7860**

### Lancement via Docker

```bash
docker build -t sofia-rag .
docker run -p 7860:7860 --env-file .env sofia-rag
```

---

## ⚙️ Variables d'environnement

Copier `.env.example` en `.env` et renseigner :

```env
# L'une ou l'autre suffit (GOOGLE_API_KEY prioritaire)
GOOGLE_API_KEY=your-google-api-key
GEMINI_API_KEY=your-gemini-api-key

# Port du serveur (optionnel, défaut : 7860)
PORT=7860
```

---

## 🔧 Paramètres RAG

| Paramètre | Valeur | Justification |
|---|---|---|
| `chunk_size` | 700 | Bon compromis entre contexte et précision sémantique |
| `chunk_overlap` | 150 | Évite de couper une compétence entre deux chunks |
| `k` (retriever) | 8 | Couvre davantage de compétences potentiellement liées |
| `score_threshold` | 80.0 | Distance FAISS max pour retenir un chunk |
| Embedding | MiniLM-L12-v2 multilingue | Optimisé pour le français, léger, 100% local |
| LLM | Gemini 2.5 Flash | Rapide, multilingue, streaming natif |
| Température | 0 | Réponses factuelles et reproductibles |

---

## 💡 Exemples de questions à poser

### Scénario 1 — Projet complet
> *"Mon projet déploie une API FastAPI avec Docker et un pipeline CI/CD GitHub Actions. Quelles compétences RNCP couvre-t-il ?"*

**Résultat attendu** : Sofia identifie les compétences liées au développement API, la conteneurisation et l'intégration continue, avec citation du référentiel.

### Scénario 2 — Projet incomplet
> *"J'ai entraîné un modèle de classification d'images avec TensorFlow mais je n'ai ni déploiement ni documentation technique. Quelles compétences me manquent ?"*

**Résultat attendu** : Sofia liste explicitement les compétences non couvertes (déploiement, MLOps, documentation) et suggère des améliorations prioritaires.

### Autres questions supportées
1. *"La compétence C11 est-elle validée si mon projet inclut un dashboard Grafana pour le monitoring ?"*
2. *"Quelles compétences me manquent pour valider le bloc MLOps ?"*

---

## ☁️ Déploiement GCP Cloud Run

```bash
# Build et push vers Google Container Registry
docker build -t gcr.io/<PROJECT_ID>/sofia-rag:latest .
docker push gcr.io/<PROJECT_ID>/sofia-rag:latest

# Déployer / mettre à jour le service Cloud Run
gcloud run deploy sofia-rag \
  --image gcr.io/<PROJECT_ID>/sofia-rag:latest \
  --region europe-west1 \
  --platform managed
```

> ⚠️ La variable `GEMINI_API_KEY` doit être configurée dans les **secrets Cloud Run**, pas dans `.env` (non versionné).

---

## 🗂️ Ingestion du référentiel (construction de l'index)

L'index FAISS doit être construit **une seule fois** avant le premier lancement, ou rechargé si le PDF change.

```bash
# 1. Placer le PDF du référentiel dans rag/data/
# 2. Lancer le script d'ingestion :
python ingest.py
```

Le script exécute les 4 étapes du pipeline RAG :

```
[1/4] LOAD   → Chargement des PDFs depuis rag/data/
[2/4] SPLIT  → Découpage en chunks (taille=700, overlap=150)
[3/4] EMBED  → Génération des embeddings (MiniLM-L12-v2)
[4/4] STORE  → Sauvegarde de l'index dans rag/index/
```

Une fois l'ingestion terminée, lancer l'application :

```bash
python app.py
```

---

## 👤 Auteur

**Gautier Gavat** — Projet réalisé dans le cadre de la formation **Développeur en Intelligence Artificielle** chez [Simplon](https://simplon.co/).