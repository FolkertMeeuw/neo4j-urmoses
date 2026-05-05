from py2neo import Graph
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Verbindung zur Neo4j Instanz
graph = Graph("bolt://localhost:7687", auth=("neo4j", "password"))

print("Bereinige alte semantische Verknüpfungen...")
graph.run("MATCH ()-[r:SEMANTICALLY_RELATED]->() DELETE r")

print("Lade frische Vektoren aus der Datenbank...")
chats = graph.run(
    "MATCH (ch:ChatHistory) WHERE ch.embedding IS NOT NULL RETURN id(ch) as id, ch.name as name, ch.embedding as vec").data()
chunks = graph.run("MATCH (c:Chunk) WHERE c.embedding IS NOT NULL RETURN id(c) as id, c.embedding as vec").data()

if not chats or not chunks:
    print("Fehler: Keine Vektoren zum Vergleichen gefunden!")
    exit()

print(f"Starte mathematischen Abgleich: {len(chats)} Chats vs. {len(chunks)} PDF-Chunks...")

links_created = 0
for chat in chats:
    # Chat-Vektor vorbereiten
    chat_vec = np.array(chat['vec'], dtype=np.float32).reshape(1, -1)

    for chunk in chunks:
        # Chunk-Vektor vorbereiten
        chunk_vec = np.array(chunk['vec'], dtype=np.float32).reshape(1, -1)

        # Ähnlichkeit berechnen (0.0 bis 1.0)
        score = float(cosine_similarity(chat_vec, chunk_vec)[0][0])

        # Qualitätshürde: Nur Verknüpfungen über 0.4 Score erstellen
        if score > 0.4:
            graph.run("""
                MATCH (ch), (c)
                WHERE id(ch) = $ch_id AND id(c) = $c_id
                MERGE (ch)-[r:SEMANTICALLY_RELATED]->(c)
                SET r.score = $score
            """, ch_id=chat['id'], c_id=chunk['id'], score=score)
            links_created += 1

print(f"\nAbgeschlossen! {links_created} hochwertige semantische Beziehungen erstellt.")
print("Du kannst die Ergebnisse jetzt in Safari mit den hohen Scores prüfen.")