import json
import os
import re
from py2neo import Graph, Node, Relationship

# Konfiguration
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"
TARGET_DIR = "/Users/folkertmeeuw/PycharmProjects/neo4j-urmoses/data"


def hole_alle_json_dateien():
    """Gibt eine Liste aller JSON-Dateipfade im Zielverzeichnis zurück."""
    return [os.path.join(TARGET_DIR, f) for f in os.listdir(TARGET_DIR) if f.endswith('.json')]


def zerlege_textblock(volltext):
    abschnitte = []
    # Split bei 'Du hast gesagt', behält den Trenner
    teile = re.split(r'(Du hast gesagt)', volltext)

    if teile:
        abschnitte.append({'role': 'metadata', 'text': teile[0].strip()})

    for i in range(1, len(teile), 2):
        if i + 1 < len(teile):
            inhalt = teile[i + 1].strip()
            abschnitte.append({'role': 'user', 'text': inhalt})

    return [a for a in abschnitte if a['text']]


def extrahiere_daten(dateipfad):
    with open(dateipfad, 'r', encoding='utf-8') as f:
        try:
            daten = json.load(f)
        except json.JSONDecodeError:
            print(f"Fehler: {dateipfad} ist kein gültiges JSON.")
            return []

    extrahiert = []
    konversation = daten.get('conversation', [])

    for eintrag in konversation:
        roh_inhalt = eintrag.get('content', '')
        if roh_inhalt:
            segmente = zerlege_textblock(roh_inhalt)
            for nr, seg in enumerate(segmente):
                extrahiert.append({
                    'index': nr,
                    'role': seg['role'],
                    'text': seg['text']
                })
    return extrahiert


def in_neo4j_speichern(chat_daten, dateiname, graph):
    try:
        # Cleanup für die spezifische Datei (verhindert Dubletten bei erneutem Run)
        graph.run("MATCH (s:ChatSession {filename: $f}) DETACH DELETE s", f=dateiname)

        session_node = Node("ChatSession", filename=dateiname)
        graph.create(session_node)

        for msg in chat_daten:
            msg_node = Node(
                "Message",
                role=msg['role'],
                text=msg['text'],
                index=msg['index']
            )
            graph.create(msg_node)
            graph.create(Relationship(session_node, "HAS_MESSAGE", msg_node))

        print(f"Erfolg: {len(chat_daten)} Segmente aus {dateiname} importiert.")

    except Exception as e:
        print(f"Fehler bei Neo4j (Datei: {dateiname}): {e}")


def main():
    graph = Graph(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    alle_pfade = hole_alle_json_dateien()

    if not alle_pfade:
        print("Keine JSON-Dateien im Verzeichnis gefunden.")
        return

    print(f"Starte Import von {len(alle_pfade)} Dateien...")

    for pfad in alle_pfade:
        dateiname = os.path.basename(pfad)
        daten = extrahiere_daten(pfad)
        if daten:
            in_neo4j_speichern(daten, dateiname, graph)


if __name__ == "__main__":
    main()