# Guide d'exécution des tests

Ce guide explique comment exécuter les tests unitaires pour les modèles de base de données de SCIRAG.

## Méthode 1 : Tests avec SQLite en mémoire (recommandé)

Cette méthode ne nécessite pas d'installation de PostgreSQL et est parfaite pour des tests rapides :

### Sur Windows (PowerShell ou Git Bash)

```bash
# Activez l'environnement virtuel
cd backend
.\.venv\Scripts\activate

# Méthode 1 : Utiliser le script Python
python scripts/run_tests.py

# OU Méthode 2 : Exécuter avec pytest directement
$env:DATABASE_URL="sqlite:///:memory:"
pytest tests/ -v
```

### Sur Linux/MacOS

```bash
# Activez l'environnement virtuel
cd backend
source .venv/bin/activate

# Méthode 1 : Utiliser le script bash
chmod +x run_tests.sh
./run_tests.sh

# OU Méthode 2 : Exécuter avec pytest directement
export DATABASE_URL="sqlite:///:memory:"
pytest tests/ -v
```

## Méthode 2 : Tests avec PostgreSQL (pour tester avec la vraie base de données)

Cette méthode nécessite une installation de PostgreSQL avec l'extension pgvector :

### 1. Démarrer PostgreSQL avec Docker

```bash
# À la racine du projet
docker-compose up -d
```

### 2. Initialiser la base de données

```bash
# Dans le dossier backend
cd backend
.\.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/MacOS

python scripts/init_test_db.py
```

### 3. Exécuter les tests

```bash
# Assurez-vous que votre fichier .env a les bonnes informations de connexion
# DATABASE_URL=postgresql://postgres:postgres@localhost:5432/scirag

pytest tests/ -v
```

## Résolution des problèmes

### Problème : "connection to server at 'localhost' failed"

**Solution** : Assurez-vous que Docker est en cours d'exécution et que les conteneurs PostgreSQL sont démarrés :

```bash
docker ps
```

### Problème : "no password supplied"

**Solution** : Vérifiez votre fichier `.env` et assurez-vous que DATABASE_URL contient le mot de passe correct :

```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/scirag
```

### Problème : "extension