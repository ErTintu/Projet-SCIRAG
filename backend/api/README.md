# API Routes pour SCIRAG

Ce dossier contient les routes API pour l'application SCIRAG.

## Structure

```
api/
├── __init__.py        # Initialisation et routeur principal
├── deps.py            # Dépendances partagées (ex: get_db)
├── schemas/           # Schémas Pydantic pour validation
│   ├── __init__.py
│   ├── conversation.py
│   ├── llm.py
│   ├── rag.py
│   └── note.py
└── routes/            # Routeurs API
    ├── __init__.py
    ├── conversations.py
    ├── llm.py
    ├── rag.py
    └── notes.py
```

## Routes principales

### Conversations
- `GET /api/conversations` - Liste des conversations
- `POST /api/conversations` - Créer une conversation
- `GET /api/conversations/{id}` - Détails d'une conversation
- `PUT /api/conversations/{id}` - Modifier une conversation
- `DELETE /api/conversations/{id}` - Supprimer une conversation
- `POST /api/conversations/{id}/send` - Envoyer un message et obtenir une réponse

### LLM Configurations
- `GET /api/llm/configs` - Liste des configurations LLM
- `POST /api/llm/configs` - Créer une configuration LLM
- `GET /api/llm/configs/{id}` - Détails d'une configuration LLM
- `PUT /api/llm/configs/{id}` - Modifier une configuration LLM
- `DELETE /api/llm/configs/{id}` - Supprimer une configuration LLM
- `GET /api/llm/providers` - Liste des fournisseurs LLM disponibles

### RAG Corpus
- `GET /api/rag/corpus` - Liste des corpus RAG
- `POST /api/rag/corpus` - Créer un corpus RAG
- `GET /api/rag/corpus/{id}` - Détails d'un corpus RAG
- `PUT /api/rag/corpus/{id}` - Modifier un corpus RAG
- `DELETE /api/rag/corpus/{id}` - Supprimer un corpus RAG
- `POST /api/rag/corpus/{id}/upload` - Uploader un document dans un corpus
- `GET /api/rag/search` - Recherche sémantique dans les corpus

### Notes
- `GET /api/notes` - Liste des notes
- `POST /api/notes` - Créer une note
- `GET /api/notes/{id}` - Détails d'une note
- `PUT /api/notes/{id}` - Modifier une note
- `DELETE /api/notes/{id}` - Supprimer une note
- `GET /api/notes/search` - Recherche sémantique dans les notes

## Comment tester

### 1. Lancer l'API

```bash
cd backend
uvicorn main:app --reload
```

L'API sera accessible à http://localhost:8000.

### 2. Documentation OpenAPI

La documentation interactive est disponible à http://localhost:8000/docs.

### 3. Script de test automatisé

Un script de test est disponible pour vérifier les principales routes :

```bash
cd backend
python scripts/test_api.py
```

Ce script permet de :
- Créer une configuration LLM
- Créer une conversation
- Créer une note
- Créer un corpus RAG
- Envoyer un message et recevoir une réponse

## Remarques sur l'implémentation

### ToDo (à implémenter dans les prochaines PR)

- Implémentation des services LLM pour connection aux API Claude, OpenAI, etc.
- Intégration de ChromaDB pour la recherche vectorielle
- Service de chunking et d'embeddings pour les documents et les notes
- Gestion des fichiers et des uploads
- Implémentation complète du RAG

### Schémas de données

Les schémas Pydantic assurent la validation des données entrantes et sortantes, avec :
- Schémas de base pour les champs communs
- Schémas spécifiques pour la création (`*Create`)
- Schémas spécifiques pour les mises à jour (`*Update`)
- Schémas de réponse (`*Response`)

### Dépendances

Les dépendances communes (comme la session de base de données) sont centralisées dans `deps.py`.

## Prochaines étapes

1. Implémenter les services LLM
2. Intégrer ChromaDB
3. Développer le service RAG complet
4. Implémenter la gestion des fichiers
5. Ajouter des tests unitaires