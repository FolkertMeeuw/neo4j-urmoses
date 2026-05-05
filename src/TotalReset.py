from py2neo import Graph

# Verbindung zu deiner Instanz auf dem MacBook Pro
graph = Graph("bolt://localhost:7687", auth=("neo4j", "password"))

def total_reset():
    print("ACHTUNG: Lösche den gesamten Graphen...")
    # Löscht alle Knoten und alle Beziehungen unwiderruflich
    graph.run("MATCH (n) DETACH DELETE n")
    print("Datenbank ist jetzt leer. Tabula Rasa.")

if __name__ == "__main__":
    confirm = input("Bist du sicher, dass du ALLES löschen willst? (j/n): ")
    if confirm.lower() == 'j':
        total_reset()
    else:
        print("Abgebrochen.")