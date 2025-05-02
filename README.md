# 🧠 SCIRAG — Assistant conversationnel intelligent avec RAG et gestion de notes

**SCIRAG** est une application locale (ou hybride) de chat intelligent basée sur les LLMs (Claude, GPT, etc.), enrichie par la recherche de documents via RAG (Retrieval-Augmented Generation) et l'intégration de notes personnelles activables.

---

## 🚀 Fonctionnalités principales

- 🔁 Conversations persistantes et organisées  
- 📂 Intégration de documents PDF dans des corpus RAG  
- 🗒️ Ajout de notes personnelles utilisables comme sources RAG  
- 🧠 Prise en charge de modèles LLM :
  - Locaux via [LM Studio](https://lmstudio.ai/)
  - API (Claude, OpenAI, Cohere, etc.)
- 🧬 Embedding et recherche vectorielle avec stockage local (ChromaDB)
- 🧪 Interface en ligne de commande (CLI) ou frontend web (optionnel)

---

## 🧱 Stack technique

| Composant         | Technologie               |
|-------------------|---------------------------|
| Backend API       | FastAPI                   |
| Base de données   | PostgreSQL ou SQLite      |
| Vector Store      | ChromaDB                  |
| Embeddings        | OpenAI / modèle local     |
| Modèles LLM       | LM Studio / API externes  |
| Frontend (option) | Next.js / React           |

---

## 📁 Structure du projet

SCIRAG/
├── api/ # Endpoints FastAPI
├── db/ # Schémas, modèles, migrations
├── rag/ # PDF reader, chunker, embedder
├── llm/ # Intégration des modèles LLM
├── notes/ # Gestion des notes + embeddings
├── tests/ # Tests unitaires et fonctionnels
├── scripts/ # Scripts divers
└── README.md

---

## ⚙️ Installation

### 1. Pré-requis

- Python 3.10+
- Node.js (si frontend)
- PostgreSQL ou SQLite
- [LM Studio](https://lmstudio.ai/) pour les modèles locaux
- (Facultatif) Clé API : OpenAI, Claude, Cohere…

### 2. Cloner et installer

```bash
git clone https://github.com/votre-org/SCIRAG.git
cd SCIRAG
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
3. Configuration
Créez un fichier .env à la racine :
DATABASE_URL=postgresql://user:pass@localhost:5432/SCIRAG
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=...
LM_STUDIO_URL=http://localhost:1234/v1
________________________________________
▶️ Lancement
uvicorn api.main:app --reload
•	Accédez à http://localhost:8000/docs pour tester l'API via Swagger.
________________________________________
🧠 Utilisation
•	Créez une conversation
•	Chargez un dossier PDF → création RAG
•	Créez et activez des notes dans les conversations
•	Sélectionnez un modèle LLM (local ou distant)
•	Envoyez un prompt → LLM répond avec contexte enrichi
________________________________________
🧪 Tests
pytest tests/
________________________________________
📚 Documentation
•	📄 Documentation Technique
•	📄 Spécifications Fonctionnelles
•	📄 Guide Installation
________________________________________
🗓️ TODO
•	 Interface CLI interactive
•	 Import/export de conversations
•	 Auth multi-utilisateur
•	 UI React / Next.js
________________________________________
👤 Auteur
Projet par Erwan Tinturier
Chef de projet & Prompt Engineer
________________________________________
⚖️ Licence
MIT
