#!/bin/zsh
# URMOSES Ressourcen-Manager

echo "=== Schritt 1: Neo4j-Urmoses Container aktivieren ==="
docker start neo4j-urmoses
sleep 5

echo "\n=== Schritt 2: Lokalen Ollama-Server im Hintergrund starten & Modell laden ==="
nohup ollama serve > /dev/null 2>&1 &
sleep 5
ollama pull nomic-embed-text
ollama pull phi3:mini

echo "\n=== Schritt 3: Echte Embeddings & Imports generieren ==="
# ChatEinlesen.py übernimmt das saubere PDF-Parsing inklusive Embeddings
python3 src/ChatEinlesen.py
# Hier betten wir direkt dein neues Brainstorming-Skript für die LA-Artefakte ein
python3 src/BrainstormingEinlesen.py

echo "\n=== Schritt 4: Mathematischen und semantischen Abgleich starten ==="
python3 src/WissenVerknuepfen.py

echo "\n=== Schritt 5: Lokalen Ollama-Server stoppen ==="
killall ollama

echo "\n=== Schritt 6: Pipeline-Validierung über Integrationstest ==="
python3 test/GraphTest.py