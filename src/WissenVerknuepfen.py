from py2neo import Graph
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

graph = Graph("bolt://localhost:7687", auth=("neo4j", "password"))

print("=== Start: Mathematischer und semantischen Abgleich ===")

print("Bereinige alte semantische Verknüpfungen...")
graph.run("MATCH ()-[r:SEMANTICALLY_RELATED]->() DELETE r")

print("Lade frische Vektoren aus der Datenbank...")
nodes = graph.run(
    """
    MATCH (n) 
    WHERE n.embedding IS NOT NULL 
    RETURN id(n) as id, labels(n)[0] as label, n.text as text, n.embedding as vec, n.quelle as quelle
    """
).data()

if len(nodes) < 2:
    print(f"Fehler: Zu wenige Vektoren gefunden (Anzahl: {len(nodes)}).")
    exit()

print(f"Erfolgreich geladen: {len(nodes)} Knoten.")
links_created = 0

for i in range(len(nodes)):
    vec_i = np.array(nodes[i]['vec'], dtype=np.float32).reshape(1, -1)
    label_i = nodes[i]['label']
    quelle_i = nodes[i].get('quelle', 'Unbekannt')

    for j in range(i + 1, len(nodes)):
        if nodes[i]['id'] == nodes[j]['id'] or (
                nodes[i].get('quelle') and nodes[i]['quelle'] == nodes[j].get('quelle')):
            continue

        vec_j = np.array(nodes[j]['vec'], dtype=np.float32).reshape(1, -1)
        label_j = nodes[j]['label']

        score = float(cosine_similarity(vec_i, vec_j)[0][0])

        if score > 0.45:
            reason_str = f"Mathematischer Match ({label_i} <-> {label_j})"
            graph.run(
                """
                MATCH (a), (b)
                WHERE id(a) = $id_a AND id(b) = $id_b
                MERGE (a)-[r:SEMANTICALLY_RELATED]->(b)
                SET r.score = $score, r.reason = $reason
                """,
                id_a=int(nodes[i]['id']),
                id_b=int(nodes[j]['id']),
                score=score,
                reason=reason_str
            )
            links_created += 1

print(f"Abgeschlossen! {links_created} Beziehungen erstellt.")