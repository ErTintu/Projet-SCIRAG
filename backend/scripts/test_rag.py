import os
import sys
sys.path.insert(0, os.path.abspath('.'))  # Ajoute le répertoire courant au path

from db.connection import SessionLocal
from rag.service import get_rag_service
from rag.chunker import ChunkerFactory, Chunk

# Créer une session de base de données
db = SessionLocal()

try:
    # Initialiser le service RAG
    print("Initialisation du service RAG...")
    rag_service = get_rag_service(db_session=db)
    
    # Tester le chunking
    print("\n=== Test du chunking ===")
    chunker = ChunkerFactory.get_chunker(strategy="paragraph")
    text = """Ceci est un premier paragraphe de test.

Ceci est un deuxième paragraphe.

Et voici un troisième paragraphe pour tester le chunking."""
    
    chunks = chunker.chunk_text(text, source_id=999, source_type="test")
    print(f"Nombre de chunks: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i}: {chunk.text}")
    
    # Tester l'embedding
    print("\n=== Test d'embedding ===")
    print("Génération des embeddings...")
    embeddings = rag_service.embedder.embed_texts([chunk.text for chunk in chunks])
    print(f"Dimension des embeddings: {embeddings[0].shape}")
    
    # Tester la recherche
    print("\n=== Test de recherche ===")
    print("Ajout des chunks à l'index...")
    chunk_embeddings = list(zip(chunks, embeddings))
    rag_service.vector_store.add_chunks([c for c, _ in chunk_embeddings], 
                                       [e for _, e in chunk_embeddings])
    
    # Ensuite, faire une recherche
    print("Recherche de 'paragraphe de test'...")
    results, _ = rag_service.search("paragraphe de test", limit=2)
    print(f"Nombre de résultats: {len(results)}")
    for i, result in enumerate(results):
        print(f"Résultat {i} (score: {result.score:.4f}): {result.chunk.text}")
    
    # Obtenir les statistiques
    stats = rag_service.get_statistics()
    print("\n=== Statistiques du RAG ===")
    for key, value in stats.items():
        print(f"  {key}: {value}")

except Exception as e:
    print(f"ERREUR: {e}")
    import traceback
    traceback.print_exc()

finally:
    db.close()
    print("\nTest terminé.")