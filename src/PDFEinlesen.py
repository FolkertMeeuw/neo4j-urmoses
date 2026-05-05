import os
import fitz
from py2neo import Graph

graph = Graph("bolt://localhost:7687", auth=("neo4j", "password"))
pfad = "/Users/folkertmeeuw/PycharmProjects/neo4j-urmoses/data"


def start():
    # Löscht alte Fragmente, um Platz für saubere Daten zu machen
    graph.run("MATCH (c:Chunk) DETACH DELETE c")

    for datei in os.listdir(pfad):
        if datei.endswith(".pdf"):
            print(f"Lese PDF: {datei}")
            doc = fitz.open(os.path.join(pfad, datei))

            for seite in doc:
                text = seite.get_text().strip()

                # Wir ignorieren zu kurze Seiten oder den bekannten Header-Müll
                if len(text) < 200 or "fundamental problem" in text.lower():
                    continue

                graph.run("""
                    CREATE (c:Chunk {
                        inhalt: $t, 
                        quelle: $s, 
                        seite: $p
                    })
                """, t=text, s=datei, p=seite.number)


if __name__ == "__main__":
    start()
    print("Fertig! PDFs sind nun ohne Müll im System.")