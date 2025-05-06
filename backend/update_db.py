"""Script pour mettre à jour le schéma de la base de données."""
import os
import sys
from dotenv import load_dotenv
import psycopg2

# Charger les variables d'environnement
load_dotenv()

# Récupérer la connexion à la base de données
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/scirag")

# Extraire les composants de l'URL
url_parts = DATABASE_URL.replace("postgresql://", "").split("/")
connection_string = url_parts[0]
db_name = url_parts[1] if len(url_parts) > 1 else "scirag"

# Extraire utilisateur, mot de passe, hôte et port
if "@" in connection_string:
    auth, host_port = connection_string.split("@")
    user, password = auth.split(":") if ":" in auth else (auth, "")
else:
    user, password = "postgres", "postgres"
    host_port = connection_string

host, port = host_port.split(":") if ":" in host_port else (host_port, "5432")

try:
    # Connexion à la base de données
    print(f"Connexion à {host}:{port} en tant que {user}...")
    conn = psycopg2.connect(
        dbname=db_name,
        user=user,
        password=password,
        host=host,
        port=port
    )
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Mise à jour des tables
    print("Mise à jour de la table note_chunks...")
    cursor.execute("ALTER TABLE note_chunks ALTER COLUMN embedding TYPE vector(1536);")
    
    print("Mise à jour de la table document_chunks...")
    cursor.execute("ALTER TABLE document_chunks ALTER COLUMN embedding TYPE vector(1536);")
    
    print("Mise à jour du schéma terminée avec succès!")
    
    # Fermeture des connexions
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Erreur lors de la mise à jour du schéma: {e}")
    sys.exit(1)