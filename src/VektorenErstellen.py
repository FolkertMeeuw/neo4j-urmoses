from py2neo import Graph
from sentence_transformers import SentenceTransformer

graph = Graph("bolt://localhost:7687", auth=("neo4j", "password"))
model = SentenceTransformer('all-MiniLM-L6-v2')


def vektorisieren():
    print("Suche nach Texten ohne Vektoren...")

    # 1. PDF-Inhalte (Chunks) verarbeiten
    chunks = graph.run("MATCH (c:Chunk) WHERE c.embedding IS NOT NULL RETURN c").data()
    # Nur wenn wirklich neue da sind oder wir alle neu machen wollen:
    # (Hier zur Sicherheit: Alle Chunks ohne Vektoren)
    targets = graph.run(
        "MATCH (n) WHERE (n:Chunk OR n:ChatHistory) AND n.embedding IS NULL RETURN n, labels(n)[0] as type").data()

    if not targets:
        print("Alles bereits vektorisiert.")
        return

    print(f"Berechne Vektoren für {len(targets)} Knoten...")
    for item in targets:
        node = item['n']
        # Wir nehmen 'inhalt' bei Chunks oder 'content' bei Chats
        text = node.get('inhalt') or node.get('content') or node.get('name')

        if text:
            vector = model.encode(text).tolist()
            graph.run(f"MATCH (n) WHERE id(n) = $id SET n.embedding = $v", id=node.identity, v=vector)


if __name__ == "__main__":
    vektorisieren()
    print("Vektoren erfolgreich erstellt.")