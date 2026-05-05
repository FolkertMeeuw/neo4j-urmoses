from py2neo import Graph

# Verbindung zum Docker-Container
graph = Graph("bolt://localhost:7687", auth=("neo4j", "password"))

# Den Status eines Tasks via Python ändern
query = """
MATCH (t:Task {name: 'Model Training'})
SET t.status = 'in_progress', t.color = 'orange'
RETURN t.name, t.status
"""

result = graph.run(query).data()
print(f"Update für URMOSES: {result}")