# Phase 4.1 : Implémentation du Service LLM pour SCIRAG

## Description

Cette PR implémente le service LLM (Large Language Model) pour l'application SCIRAG, permettant de connecter l'application à différents fournisseurs de modèles de langage, notamment:

- **Anthropic Claude** (via l'API Anthropic)
- **OpenAI GPT** (via l'API OpenAI)
- **Modèles locaux** (via LM Studio)

L'architecture implémentée suit un design flexible permettant d'ajouter facilement d'autres fournisseurs à l'avenir.

## Fichiers implémentés

- `backend/llm/base.py` - Classe abstraite définissant l'interface commune
- `backend/llm/providers/anthropic.py` - Implémentation pour Anthropic Claude
- `backend/llm/providers/openai.py` - Implémentation pour OpenAI GPT
- `backend/llm/providers/local.py` - Implémentation pour LM Studio (local)
- `backend/llm/router.py` - Routeur central pour la sélection des providers
- `backend/llm/__init__.py` - Initialisation et exportation
- `backend/tests/test_llm_service.py` - Tests unitaires

## Guide de test et d'utilisation

### Prérequis

1. Avoir configuré le fichier `.env` avec les clés API nécessaires:
   ```
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-...
   LM_STUDIO_URL=http://localhost:1234/v1
   ```

2. S'assurer que les dépendances sont installées:
   ```bash
   pip install anthropic openai httpx pytest pytest-asyncio
   ```

### Lancer les tests

Pour lancer les tests unitaires:

```bash
cd backend
python -m pytest tests/test_llm_service.py -v
```

### Utilisation du service

Le service LLM s'intègre automatiquement à l'application FastAPI au démarrage. Pour l'utiliser dans un autre module:

```python
from llm import router as llm_router

# Exemple d'utilisation
async def example_function():
    # Configuration
    config = {
        "provider": "anthropic",  # ou "openai", "local"
        "model_name": "claude-3-sonnet-20240229",
        "temperature": 0.7,
        "max_tokens": 1024
    }
    
    # Génération de réponse
    response = await llm_router.generate_response(
        config=config,
        prompt="Quelle est la capitale de la France?",
        system_prompt="Tu es un assistant utile et concis."
    )
    
    # Utilisation de la réponse
    print(response["content"])
```

### Vérifier la disponibilité des providers

Pour vérifier les providers disponibles:

```bash
cd backend
python -c "import asyncio, sys; sys.path.append('.'); from llm import router; asyncio.run(async def main(): await router.initialize(); providers = await router.get_available_providers(); print(providers); return providers)())"
```

## Notes techniques

- Le service gère automatiquement les erreurs d'API et les réessaie si nécessaire
- L'interface est unifiée pour tous les fournisseurs
- La configuration est chargée depuis la base de données ou passée directement
- Le service supporte l'ajout de providers personnalisés

## Prochaines étapes

Après validation du service LLM, nous passerons à:
1. Implémentation du service de fichiers (extraction de texte des PDFs)
2. Implémentation du service RAG (chunking, embeddings, recherche vectorielle)

## Références

- [Documentation API Anthropic](https://docs.anthropic.com/claude/reference/getting-started-with-the-api)
- [Documentation API OpenAI](https://platform.openai.com/docs/api-reference)
- [Documentation LM Studio](https://lmstudio.ai/docs)
```