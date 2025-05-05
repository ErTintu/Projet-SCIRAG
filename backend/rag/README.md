# Phase 4.2 : Service de Fichiers pour SCIRAG

## Description

Cette PR implémente le Service de Fichiers pour l'application SCIRAG, offrant les fonctionnalités nécessaires à l'extraction de texte à partir de documents PDF et à la gestion des fichiers uploadés. Ce service est critique pour le futur système RAG, car il fournit les données textuelles qui seront transformées en embeddings et utilisées pour la recherche sémantique.

## Fonctionnalités implémentées

- **Extraction de texte PDF complète** (support des métadonnées, extraction page par page)
- **Gestion des fichiers uploadés** (sauvegarde, suppression, nommage unique)
- **Validation des PDF** (vérification de l'intégrité et du format)
- **Prévisualisation du contenu** (nouvelle API pour visualiser le texte par page)

## Fichiers implémentés

- `backend/rag/loader.py` - Service d'extraction de texte PDF
- `backend/rag/file_manager.py` - Gestion des fichiers uploadés
- `backend/tests/test_file_service.py` - Tests unitaires
- Modifications de `backend/api/routes/rag.py` - Intégration avec l'API existante

## Comment tester

### Prérequis

Installer les dépendances nécessaires :

```bash
pip install pypdf
```

### Tests unitaires

```bash
cd backend
python -m pytest tests/test_file_service.py -v
```

### Test manuel via l'API

1. Lancer le serveur FastAPI :
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

2. Accéder à l'interface Swagger : http://localhost:8000/docs

3. Tester les endpoints suivants :
   - POST `/api/rag/corpus/{corpus_id}/upload` - Upload d'un document PDF
   - GET `/api/rag/corpus/{corpus_id}/documents/{document_id}/preview` - Prévisualisation du contenu PDF

## Notes techniques

- Le service utilise `pypdf` pour l'extraction de texte, une bibliothèque Python pure sans dépendances externes
- L'approche implémentée est robuste face aux PDF malformés ou corrompus
- Le système de gestion de fichiers garantit des noms de fichiers uniques et sans caractères problématiques
- Les métadonnées des PDF (titre, auteur, etc.) sont extraites lorsque disponibles

## Prochaines étapes

Après validation du service de fichiers, nous passerons à l'implémentation du service RAG complet (chunking, embeddings, recherche vectorielle avec ChromaDB).