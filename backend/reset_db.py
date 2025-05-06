"""Script pour réinitialiser complètement la base de données - version alternative."""
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Récupérer l'URL de la base de données
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/scirag")

try:
    # Créer la connexion SQLAlchemy
    print(f"Connexion à la base de données avec URL: {DATABASE_URL}")
    engine = create_engine(DATABASE_URL)
    
    # Établir une connexion
    with engine.connect() as connection:
        # Désactiver les contraintes de clé étrangère temporairement
        print("Désactivation des contraintes de clé étrangère...")
        connection.execute(text("SET session_replication_role = 'replica';"))
        
        # Lister toutes les tables
        print("Récupération de la liste des tables...")
        result = connection.execute(text("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public'
        """))
        
        tables = [row[0] for row in result]
        print(f"Tables trouvées: {tables}")
        
        # Supprimer toutes les tables
        print("Suppression de toutes les tables...")
        for table in tables:
            print(f"  Suppression de {table}...")
            connection.execute(text(f"TRUNCATE TABLE {table} CASCADE;"))
        
        # Réactiver les contraintes de clé étrangère
        print("Réactivation des contraintes de clé étrangère...")
        connection.execute(text("SET session_replication_role = 'origin';"))
        
        connection.commit()
    
    print("Base de données réinitialisée avec succès!")
    
except Exception as e:
    print(f"Erreur lors de la réinitialisation de la base de données: {e}")
    import traceback
    print(traceback.format_exc())
    sys.exit(1)