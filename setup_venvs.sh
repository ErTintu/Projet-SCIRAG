#!/bin/bash

# 1. Désactivation éventuelle de l'environnement actif
deactivate 2>/dev/null || true

# 2. Suppression de l'ancien environnement .venv dans source/
if [ -d "source/.venv" ]; then
  echo "Suppression de l'environnement source/.venv ..."
  rm -rf source/.venv
  echo "Suppression terminée."
else
  echo "Aucun environnement source/.venv trouvé, rien à supprimer."
fi

# 3. Suppression des environnements backend/.venv et frontend/.venv s'ils existent
if [ -d "backend/.venv" ]; then
  echo "Suppression de backend/.venv ..."
  rm -rf backend/.venv
  echo "Suppression terminée."
else
  echo "Aucun environnement backend/.venv trouvé."
fi

if [ -d "frontend/.venv" ]; then
  echo "Suppression de frontend/.venv ..."
  rm -rf frontend/.venv
  echo "Suppression terminée."
else
  echo "Aucun environnement frontend/.venv trouvé."
fi

# 4. Création des nouveaux environnements virtuels dans backend et frontend
echo "Création de l'environnement virtuel backend/.venv ..."
python -m venv backend/.venv
echo "Environnement backend/.venv créé."

echo "Création de l'environnement virtuel frontend/.venv ..."
python -m venv frontend/.venv
echo "Environnement frontend/.venv créé."

# 5. Modification du fichier .gitignore pour ignorer les dossiers .venv dans backend et frontend
GITIGNORE=".gitignore"
echo "Ajout des dossiers .venv à .gitignore si nécessaire..."

if ! grep -q "^backend/\.venv/" "$GITIGNORE"; then
  echo "backend/.venv/" >> "$GITIGNORE"
  echo "Ajouté backend/.venv/ à .gitignore"
fi

if ! grep -q "^frontend/\.venv/" "$GITIGNORE"; then
  echo "frontend/.venv/" >> "$GITIGNORE"
  echo "Ajouté frontend/.venv/ à .gitignore"
fi

# Optionnel : suppression de source/.venv du .gitignore si présent
if grep -q "^source/\.venv/" "$GITIGNORE"; then
  sed -i.bak '/^source\/\.venv\//d' "$GITIGNORE"
  echo "Retiré source/.venv/ de .gitignore"
fi

echo "Mise à jour de .gitignore terminée."

echo "Script terminé. Tu peux maintenant activer tes environnements virtuels séparés dans backend/ et frontend/."
echo "Exemple : source backend/.venv/bin/activate (Linux/macOS) ou backend\\.venv\\Scripts\\activate (Windows)"
