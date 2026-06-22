#!/bin/zsh
# URMOSES Infrastruktur-Stopp

echo "=== Schritt 1: Lokalen Ollama-Server stoppen ==="
if pgrep -x "ollama" > /dev/null; then
    killall ollama
    echo "Ollama-Server erfolgreich beendet."
else
    echo "Ollama-Server lief nicht."
fi

echo "\n=== Schritt 2: Neo4j-Urmoses Container stoppen ==="
if [ "$(docker ps -q -f name=neo4j-urmoses)" ]; then
    docker stop neo4j-urmoses
    echo "Neo4j-Container erfolgreich heruntergefahren."
else
    echo "Neo4j-Container war bereits gestoppt oder läuft nicht."
fi

echo "\n=== Status-Check ==="
docker ps -a -f name=neo4j-urmoses

echo "\nAlles erledigt. Schönen Feierabend!"