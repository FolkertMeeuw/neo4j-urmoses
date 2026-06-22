import os
import json
import ollama
from bs4 import BeautifulSoup
from py2neo import Graph, Node
from langchain_text_splitters import RecursiveCharacterTextSplitter

graph = Graph("bolt://localhost:7687", auth=("neo4j", "password"))
# Pfad zu deinem Brainstorming-Ordner anpassen
brainstorming_pfad = "/Users/folkertmeeuw/PycharmProjects/neo4j-urmoses/brainstorming_data"

def generate_embedding(text):
    try:
        response = ollama.embeddings(model="nomic-embed-text", prompt=text)
        return response["embedding"]
    except Exception as e:
        print(f"Ollama Embedding-Fehler: {e}")
        return [0.0] * 768

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)

def extrahiere_text(dateipfad, endung):
    """Extrahiert reinen Text je nach Dateityp und verwirft Code/Markup-Rauschen."""
    try:
        with open(dateipfad, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            
        if endung == ".html":
            # Extrahiert nur den sichtbaren Text von Webseiten ohne HTML-Tags
            soup = BeautifulSoup(content, "html.parser")
            return soup.get_text(separator=" ").strip()
        elif endung == ".json":
            # Macht aus JSON-Strukturen lesbaren Text für das Embedding
            try:
                daten = json.loads(content)
                return json.dumps(daten, indent=2, ensure_ascii=False)
            except:
                return content
        else:
            return content.strip()
    except Exception as e:
        print(f"Fehler beim Lesen von {dateipfad}: {e}")
        return ""

def start():
    print("Bereinige alte Brainstorming-Knoten...")
    graph.run("MATCH (b:Brainstorming) DETACH DELETE b")
    
    if not os.path.exists(brainstorming_pfad):
        print(f"Ordner nicht gefunden: {brainstorming_pfad}")
        return

    erlaubte_endungen = (".txt", ".md", ".html", ".json")
    
    for root, dirs, files in os.walk(brainstorming_pfad):
        for datei in files:
            endung = os.path.splitext(datei)[1].lower()
            if endung in erlaubte_endungen:
                vollstaendiger_pfad = os.path.join(root, datei)
                relativer_pfad = os.path.relpath(vollstaendiger_pfad, brainstorming_pfad)
                
                print(f"Verarbeite Brainstorming-Artefakt: {relativer_pfad}")
                rohtext = extrahiere_text(vollstaendiger_pfad, endung)
                
                if len(rohtext) < 50:
                    continue
                    
                chunks = text_splitter.split_text(rohtext)
                
                for idx, chunk_content in enumerate(chunks):
                    vector = generate_embedding(chunk_content)
                    
                    b_node = Node(
                        "Brainstorming",
                        quelle=relativer_pfad,
                        typ=endung.replace(".", ""),
                        chunk_id=idx,
                        text=chunk_content,
                        embedding=vector
                    )
                    graph.create(b_node)

if __name__ == "__main__":
    start()
    print("Brainstorming-Daten erfolgreich in den Graphen integriert.")