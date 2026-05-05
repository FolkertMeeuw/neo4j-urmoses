#!/bin/zsh
# URMOSES Ressourcen-Manager

# 1. Ollama-Check & Extraktion
echo "Starte Extraktion..."
# Hier dein Python Script, das NUR Ollama nutzt und in Datei schreibt
# Danach Ollama killen um RAM freizugeben
killall Ollama

# 2. Neo4j-Check & Import
echo "Starte Neo4j..."
docker start neo4j-urmoses
sleep 10 # Warten bis DB bereit
# Hier dein Python Script, das NUR die Datei in Neo4j schiebt