import os
import csv
import requests
from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "password")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GTFS_DIR = os.path.join(BASE_DIR, "data", "gtfs_bus")

LAT_VENUE = 33.9534
LON_VENUE = -118.3387
RADIUS_METERS = 2500


def hole_osm_wege():
    print("Hole reale Wege (Radwege & beruhigte Zonen) aus OSM für die letzte Meile...")
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json][timeout:90];
    (
      way["highway"="cycleway"](around:{RADIUS_METERS},{LAT_VENUE},{LON_VENUE});
      way["bicycle"="yes"](around:{RADIUS_METERS},{LAT_VENUE},{LON_VENUE});
      way["highway"="living_street"](around:{RADIUS_METERS},{LAT_VENUE},{LON_VENUE});
      way["highway"="pedestrian"](around:{RADIUS_METERS},{LAT_VENUE},{LON_VENUE});
    );
    out body;
    >;
    out skel qt;
    """
    headers = {'User-Agent': 'URMOSES_Infrastruktur_Bot/1.0 (folkert@meeuw.de)'}
    try:
        response = requests.post(overpass_url, data={'data': overpass_query}, headers=headers)
        response.raise_for_status()
        return response.json().get('elements', [])
    except Exception as e:
        print(f"Fehler beim OSM-Abruf: {e}")
        return []


def integriere_projekt_netzwerk():
    stops_file = os.path.join(GTFS_DIR, "stops.txt")
    trips_file = os.path.join(GTFS_DIR, "trips.txt")
    st_file = os.path.join(GTFS_DIR, "stop_times.txt")
    routes_file = os.path.join(GTFS_DIR, "routes.txt")

    if not all(os.path.exists(f) for f in [stops_file, trips_file, st_file, routes_file]):
        print("Fehler: Mindestens eine der GTFS-Dateien fehlt in data/gtfs_bus/")
        return

    print("Lese routes.txt für Liniennamen ein...")
    route_mapping = {}
    with open(routes_file, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            r_id = row.get("route_id")
            short_name = row.get("route_short_name")
            long_name = row.get("route_long_name")
            route_mapping[r_id] = short_name if short_name else long_name

    print("Lese trips.txt für Zuordnung Trip -> Linie ein...")
    trip_to_route_name = {}
    with open(trips_file, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            t_id = row.get("trip_id")
            r_id = row.get("route_id")
            if t_id and r_id in route_mapping:
                trip_to_route_name[t_id] = route_mapping[r_id]

    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as session:
        # 1. Schritt: Entlastung der Speicherallokation beim Löschen
        print("Bereinige alte Infrastruktur-Kanten speicherschonend...")
        while True:
            result = session.run("""
                MATCH ()-[r:NEXT_STOP|CONNECTS_TO|LEADS_TO]-()
                WITH r LIMIT 50000
                DELETE r
                RETURN count(r) AS deleted
            """)
            deleted_count = result.single()["deleted"]
            if deleted_count == 0:
                break
            print(f"  -> {deleted_count} alte Kanten gelöscht...")

        print("Bereinige alte Infrastruktur-Knoten...")
        while True:
            result = session.run("""
                MATCH (n) WHERE n:Station OR n:BikePath OR n:Venue
                WITH n LIMIT 50000
                DELETE n
                RETURN count(n) AS deleted
            """)
            deleted_count = result.single()["deleted"]
            if deleted_count == 0:
                break
            print(f"  -> {deleted_count} alte Knoten gelöscht...")

        print("Erstelle Datenbank-Index für Stationen...")
        session.run("CREATE INDEX station_id_idx IF NOT EXISTS FOR (s:Station) ON (s.station_id)")

        print("Anker anlegen...")
        session.run("""
            MERGE (v:Venue {venue_id: "sofi_stadium"})
            SET v.venue_name = "SoFi Stadium", v.lat = $lat, v.lon = $lon
        """, lat=LAT_VENUE, lon=LON_VENUE)

        print("Importiere GTFS Haltestellen...")
        with open(stops_file, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            tx = session.begin_transaction()
            count_stops = 0
            for row in reader:
                stop_id = row.get("stop_id")
                stop_name = row.get("stop_name")
                lat = row.get("stop_lat")
                lon = row.get("stop_lon")

                if stop_id and stop_name and lat and lon:
                    tx.run("""
                        MERGE (s:Station {station_id: $id})
                        SET s.station_name = $name, s.lat = toFloat($lat), s.lon = toFloat($lon), s.source = "GTFS_Bus"
                    """, id=stop_id, name=stop_name, lat=lat, lon=lon)
                    count_stops += 1
                    if count_stops % 2000 == 0:
                        tx.commit()
                        tx = session.begin_transaction()
            tx.commit()
            print(f"{count_stops} GTFS-Stationen geladen.")

        osm_elements = hole_osm_wege()
        count_paths = 0
        for el in osm_elements:
            if el.get('type') == 'way':
                tags = el.get('tags', {})
                name = tags.get('name', tags.get('highway', 'Verbindungsweg'))
                path_type = "Radweg" if tags.get("highway") == "cycleway" or tags.get(
                    "bicycle") == "yes" else "Beruhigte Straße"

                session.run("""
                    MERGE (bp:BikePath {bikepath_id: $id})
                    SET bp.bikepath_name = $name, bp.type = $type, bp.source = "OSM", bp.lat = $lat, bp.lon = $lon
                """, id=str(el['id']), name=name, type=path_type, lat=LAT_VENUE, lon=LON_VENUE)
                count_paths += 1
        print(f"{count_paths} reale Wege aus OpenStreetMap importiert.")

        print("Lese stop_times.txt performant in den Speicher...")
        trip_sequences = {}
        with open(st_file, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                trip_id = row.get("trip_id")
                stop_id = row.get("stop_id")
                seq = int(row.get("stop_sequence", 0))
                if trip_id and stop_id:
                    if trip_id not in trip_sequences:
                        trip_sequences[trip_id] = []
                    trip_sequences[trip_id].append((seq, stop_id))

        print("Bereite Kanten-Batches vor...")
        kanten_liste = []
        for trip_id, stops in trip_sequences.items():
            stops.sort()
            line_name = trip_to_route_name.get(trip_id, "Unknown")
            for i in range(len(stops) - 1):
                kanten_liste.append({
                    'id_a': stops[i][1],
                    'id_b': stops[i + 1][1],
                    'line_name': line_name
                })

        print(f"Schreibe {len(kanten_liste)} Kanten via UNWIND in Neo4j (Batch-Verarbeitung)...")
        batch_size = 20000
        for i in range(0, len(kanten_liste), batch_size):
            batch = kanten_liste[i:i + batch_size]
            session.run("""
                UNWIND $batch AS r
                MATCH (s1:Station {station_id: r.id_a})
                MATCH (s2:Station {station_id: r.id_b})
                MERGE (s1)-[n:NEXT_STOP]->(s2)
                ON CREATE SET n.lines = [r.line_name]
                ON MATCH SET n.lines = case when r.line_name in n.lines then n.lines else n.lines + r.line_name end
            """, batch=batch)
            if (i + batch_size) % 100000 == 0 or (i + batch_size) >= len(kanten_liste):
                print(f"{min(i + batch_size, len(kanten_liste))} Kanten importiert...")

        print("Verknüpfe Core-Stationen und OSM-Wege...")
        session.run("""
            MATCH (s:Station), (bp:BikePath)
            WHERE s.source = "GTFS_Bus" AND bp.source = "OSM"
              AND point.distance(point({latitude: s.lat, longitude: s.lon}), point({latitude: bp.lat, longitude: bp.lon})) < 800
            MERGE (s)-[:CONNECTS_TO]->(bp)
        """)

        session.run("""
            MATCH (bp:BikePath), (v:Venue {venue_id: "sofi_stadium"})
            WHERE bp.source = "OSM"
              AND point.distance(point({latitude: bp.lat, longitude: bp.lon}), point({latitude: v.lat, longitude: v.lon})) < 2500
            MERGE (bp)-[:LEADS_TO]->(v)
        """)

    driver.close()
    print("Linienauflösung erfolgreich abgeschlossen und Graphen-Datenbasis aktualisiert!")


if __name__ == "__main__":
    integriere_projekt_netzwerk()