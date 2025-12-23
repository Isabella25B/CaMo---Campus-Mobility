"""
Campus VVS Navigator - Backend Service

Dieses Modul stellt die zentrale REST-API für den Campus VVS Navigator bereit. 
Es dient als Middleware zwischen dem Frontend, der PostgreSQL-Datenbank und 
externen Mobilitäts- sowie Stundenplan-Schnittstellen (VVS EFA & DHBW RAPLA).

Hauptfunktionen:
    * Verbindungssuche: Intelligente Routenplanung zwischen Campus und Wohnort 
      unter Berücksichtigung von individuellen Pufferzeiten.
    * Stundenplan-Proxy: Abfrage von Vorlesungsterminen über die dhbw.app-Seite.
    * Profilverwaltung: Persistierung von Benutzereinstellungen und Favoriten 
      in einer PostgreSQL-Datenbank.
    * Echtzeit-Parsing: Verarbeitung von VVS-EFA-Daten (RapidJSON) mit 
      Fokus auf Verspätungs-Handling und Zeit-Offsets.

Architektur:
    Das Backend nutzt Flask als Web-Framework und psycopg2 für die 
    Datenbank-Interaktion. Es ist für den Betrieb in einer Docker-Umgebung 
    konzipiert (lauscht auf 0.0.0.0:5000).

Konfiguration:
    Die Konfiguration erfolgt über Umgebungsvariablen in einer .env-Datei:
    - DB_HOST, DB_NAME, DB_USER, DB_PASS, DB_PORT: Datenbank-Zugangsdaten.

Datum: Dezember 2025
Version: 1.0.0
"""

# Standard-Library Imports
import os
import csv
import json
import base64
from datetime import datetime, timedelta

# Third-Party Imports
import requests
import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

# App Initialisierung
app = Flask(__name__)
CORS(app)
load_dotenv()


# --- DATENBANK KONFIGURATION ---
db_config = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASS'),
    'dbname': os.getenv('DB_NAME'),
    'port': os.getenv('DB_PORT', '5432')
}

def get_db_connection():
    # Verbindung zu PostgreSQL aufbauen
    return psycopg2.connect(**db_config)


# --- VVS KONFIGURATION ---
BASE_URL = "https://www3.vvs.de/mngvvs/XML_TRIP_REQUEST2"
UNI_STOPS = [
    {"name": "Rosenberg-/Seidenstraße", "id": "de:08111:6072"},
    {"name": "Linden-Museum", "id": "de:08111:2196"}
]
STATIC_EFA_PARAMS = {
    "SpEncId": 0, 
    "changeSpeed": "normal", 
    "computationType": "sequence",
    "coordOutputFormat": "EPSG:4326", 
    "cycleSpeed": 14, 
    "deleteAssignedStops": 0,
    "deleteITPTWalk": 0, 
    "descWithElev": 1, 
    "itOptionsActive": 1,
    "macroWebTrip": True, 
    "noElevationProfile": 1, 
    "outputFormat": "rapidJSON",
    "outputOptionsActive": 1, 
    "ptOptionsActive": 1, 
    "routeType": "leasttime",
    "searchLimitMinutes": 360, 
    "serverInfo": 1, 
    "trITArrMOT": 100,
    "trITArrMOTvalue": 0, 
    "trITDepMOT": 100, 
    "trITDepMOTvalue": 0,
    "type_destination": "any", 
    "type_origin": "any", 
    "useElevationData": 1,
    "useLocalityMainStop": 0, 
    "useRealtime": 1, 
    "useUT": 0, 
    "version": "10.2.10.139"
}
stop_mapping = {}


# --- VVS-Funktionen ---
def load_stops():
    """
    Lädt Haltestellendaten aus einer CSV-Datei und speichert sie im globalen Mapping.

    Die Funktion liest die Datei 'haltestellen.csv' ein, die sich im selben Verzeichnis 
    wie das Skript befinden muss. Dabei werden die Spalten 'Name', 'Globale ID' und 
    optional 'Zusatz' verarbeitet (Zusatz hat einen Wert, wenn ein Name im VVS-Netz 
    mehrmals vorkommt, z.B. "Ortsmitte". In dem Fall wird zusätzlich der Teilort mitgegeben). 
    Die Daten werden in das globale Dictionary `stop_mapping` geschrieben, wobei der Name 
    (ggf. mit Zusatz) als Key und die ID als Value dient.

    Dateiformat der CSV:
        - Trennzeichen: Semikolon (;)
        - Kodierung: UTF-8 mit BOM (utf-8-sig)
        - Erwartete Header: 'Name', 'Globale ID', 'Zusatz' (optional)

    Raises:
        FileNotFoundError: Wenn die Datei 'haltestellen.csv' nicht gefunden wird.
        KeyError: Wenn die erforderlichen Spalten 'Name' oder 'Globale ID' fehlen.
        Exception: Fängt allgemeine Fehler beim Dateizugriff ab und gibt eine 
                  Fehlermeldung auf der Konsole aus.
    """
    try:
        file_path = os.path.join(os.path.dirname(__file__), 'haltestellen.csv')
        with open(file_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                name, stop_id = row['Name'].strip(), row['Globale ID'].strip()
                zusatz = row.get('Zusatz', '').strip() 
                display_name = f"{name} ({zusatz})" if zusatz else name
                stop_mapping[display_name] = stop_id
    except Exception as e:
        print(f"Fehler CSV: {e}")

load_stops()


def format_vvs_time(time_str):
    """
    Konvertiert verschiedene Zeit-Strings der VVS-API in ein lesbares Format (HH:MM).

    Die Funktion verarbeitet drei gängige Formate, die von der EFA-Schnittstelle 
    geliefert werden:
    1. ISO-8601 Zeitstempel (z. B. "2025-12-24T14:00:00Z") -> Extrahiert die Uhrzeit.
    2. Kompakte Zeit-Strings (z. B. "1400") -> Fügt einen Doppelpunkt ein.
    3. Bereits teilweise formatierte oder unbekannte Strings -> Kürzt auf 5 Zeichen.

    Args:
        time_str (str): Der zu formatierende Zeit-String. Kann None oder ein 
            nicht-String Typ sein.

    Returns:
        str: Die formatierte Uhrzeit im Format "HH:MM". 
            Gibt "--:--" zurück, falls der Input ungültig oder nicht verarbeitbar ist.

    Beispiele:
        >>> format_vvs_time("2025-12-24T14:30:00Z")
        '14:30'
        >>> format_vvs_time("0915")
        '09:15'
        >>> format_vvs_time(None)
        '--:--'
    """
    if not time_str or not isinstance(time_str, str):
        return "--:--"
    if 'T' in time_str:
        try:
            return time_str.split('T')[1][:5]
        except IndexError:
            return "--:--"
    if len(time_str) == 4 and time_str.isdigit():
        return f"{time_str[:2]}:{time_str[2:]}"
    return time_str[:5]


def parse_vvs_data(vvs_json):
    """
    Extrahiert und strukturiert relevante Verbindungsinformationen aus der VVS-API-Antwort.

    Diese Funktion transformiert das komplexe 'rapidJSON'-Format der EFA-Schnittstelle in ein 
    vereinfachtes Dictionary-Format. Dabei werden Echtzeitdaten (Estimated) gegenüber 
    Plandaten (Planned) bevorzugt behandelt.

    Verarbeitungsschritte:
        1. Validierung der API-Antwort auf vorhandene 'journeys'.
        2. Iteration über jede Fahrt (Journey) und deren Teilstrecken (Legs).
        3. Extraktion von Abfahrts- und Ankunftszeiten (bevorzugt Realtime-Daten).
        4. Berechnung der Gesamtdauer basierend auf der Differenz zwischen erstem 
           Start und letzter Ankunft (mit Handling für Tagesübergänge).
        5. Mapping der Transportmittel (Liniennummer oder Kennzeichnung als Fußweg).

    Args:
        vvs_json (dict): Die unbearbeitete JSON-Antwort der VVS-EFA-API.

    Returns:
        list[dict]: Eine Liste prozessierter Verbindungen. Jedes Dictionary enthält:
            - 'dep' (str): Startzeitpunkt (HH:MM).
            - 'arr' (str): Ankunftszeitpunkt (HH:MM).
            - 'duration' (int): Gesamtreisedauer in Minuten.
            - 'interchanges' (int): Anzahl der Umstiege.
            - 'sections' (list): Details zu den einzelnen Fahrtabschnitten (Linie, Start, Ziel, Zeiten).

    Raises:
        datetime.ValueError: Kann intern bei fehlerhaften Zeitformaten auftreten, 
                            wird jedoch durch ein Fallback auf API-Dauerwerte abgefangen.
    """
    processed = []
    if not vvs_json or 'journeys' not in vvs_json:
        return []

    for journey in vvs_json.get('journeys', []):
        legs = journey.get('legs', [])
        if not legs: continue
        
        sections = []
        for leg in legs:
            origin = leg.get('origin', {})
            destination = leg.get('destination', {})
            dep_raw = (leg.get('departureTimeEstimated') or leg.get('departureTimePlanned') or 
                       origin.get('departureTimeEstimated') or origin.get('departureTimePlanned'))
            arr_raw = (leg.get('arrivalTimeEstimated') or leg.get('arrivalTimePlanned') or 
                       destination.get('arrivalTimeEstimated') or destination.get('arrivalTimePlanned'))

            sections.append({
                "line": leg.get('transportation', {}).get('number', "Fußweg"),
                "from": origin.get('name', 'Unbekannt'),
                "to": destination.get('name', 'Unbekannt'),
                "departure": format_vvs_time(dep_raw),
                "arrival": format_vvs_time(arr_raw)
            })

        first_dep = sections[0]['departure']
        last_arr = sections[-1]['arrival']
        duration_minutes = 0
        try:
            t1 = datetime.strptime(first_dep, "%H:%M")
            t2 = datetime.strptime(last_arr, "%H:%M")
            delta = t2 - t1
            seconds = delta.total_seconds()
            if seconds < 0:
                seconds += 86400 
            duration_minutes = int(seconds / 60)
        except Exception:
            duration_minutes = journey.get('duration', 0) // 60

        processed.append({
            "dep": first_dep,
            "arr": last_arr,
            "duration": duration_minutes,
            "interchanges": journey.get('interchanges', 0),
            "sections": sections
        })
    return processed


# --- HILFSFUNKTIONEN ---
def get_username_from_token(token):
    if not token: return None
    try:
        token_clean = token.split(" ")[1] if " " in token else token
        payload_b64 = token_clean.split('.')[1]
        payload_b64 += '=' * (-len(payload_b64) % 4)
        return json.loads(base64.b64decode(payload_b64).decode('utf-8')).get('sub')
    except: return None



# --- API ROUTEN ---
# - VVS -
@app.route('/api/stops')
def get_stops():
    """
    Gibt eine Liste aller verfügbaren Haltestellen für das Frontend zurück.

    Dieser Endpunkt transformiert das interne `stop_mapping` Dictionary in ein 
    JSON-Array, das direkt für Autocomplete-Felder oder Auswahllisten im 
    Frontend (z. B. in der `suggestBox`) verwendet werden kann.

    Returns:
        Response: Ein JSON-Objekt (Liste von Dictionaries) mit:
            - name (str): Der Anzeigename der Haltestelle (inkl. Zusatz).
            - id (str): Die globale VVS-ID der Haltestelle (z. B. 'de:08111:6072').

    Example Response (JSON):
        [
            {"name": "Rosenberg-/Seidenstraße (Bstg 1)", "id": "de:08111:6072"},
            {"name": "Linden-Museum", "id": "de:08111:25"}
        ]

    Status Codes:
        200: Erfolgreiche Abfrage.
    """
    return jsonify([{"name": n, "id": i} for n, i in stop_mapping.items()])

@app.route('/api/connections')
def get_connections():
    """
    Sucht nach Verkehrsverbindungen zwischen einer Benutzer-Haltestelle und dem Campus.

    Der Endpunkt steuert die intelligente Richtungswahl und berechnet automatisch 
    Pufferzeiten für den Fußweg oder Umstiege. Er integriert zudem einen 
    Zeitzonen-Offset-Fix für die Kommunikation mit der VVS-API.

    Query-Parameter:
        mode (str): 'to_uni' (Anreise, Suche nach Ankunftszeit) oder 
                    'from_uni' (Heimreise, Suche nach Abfahrtszeit).
        userStopId (str): Die globale VVS-ID der Start- bzw. Zielhaltestelle.
        date (str): Datum der Fahrt im Format YYYYMMDD.
        time (str): Uhrzeit der Fahrt im Format HHMM.
        buffer (int, optional): Zusätzlicher Zeitpuffer in Minuten (Standard: 0).

    Logik & Zeitberechnung:
        1. Zeit-Offset: Addiert 1 Stunde auf die Anfragezeit, um Differenzen zwischen 
           Server- und API-Zeit auszugleichen (Quick-Fix).
        2. Puffer: Addiert einen festen Basis-Puffer von 10 Minuten zum Benutzer-Puffer.
        3. Richtungswahl:
            - 'to_uni': Sucht Verbindungen, die VOR (Ankunftszeit minus Puffer) ankommen.
            - 'from_uni': Sucht Verbindungen, die NACH (Abfahrtszeit plus Puffer) starten.
        4. Aggregation: Fragt Daten für alle Campus-Haltestellen (UNI_STOPS) ab.

    Returns:
        Response: JSON-Objekt mit einer Liste der 5 besten Verbindungen unter dem Key 'journeys'.

    Status Codes:
        200: Erfolgreiche Suche (auch bei leeren Ergebnissen).
        400: Ungültiges Zeitformat übergeben.
    """
    mode = request.args.get('mode')
    user_stop_id = request.args.get('userStopId')
    t_date = request.args.get('date') 
    t_time = request.args.get('time')

    try:
        user_buffer = int(request.args.get('buffer', 0))
        total_buffer_minutes = user_buffer + 10 
    except (ValueError, TypeError):
        total_buffer_minutes = 10

    results = []
    try:
        base_time = datetime.strptime(t_time, "%H%M")
        # "Quick and Dirty" Fix: 60 Minuten korrigieren
        corrected_time = base_time + timedelta(hours=1)
    except ValueError:
        return jsonify({"error": "Ungültiges Zeitformat"}), 400

    for uni in UNI_STOPS:
        if mode == 'to_uni':
            search_dt = corrected_time - timedelta(minutes=total_buffer_minutes)
            origin, dest, t_type = user_stop_id, uni["id"], "arr"
        else:
            search_dt = corrected_time + timedelta(minutes=total_buffer_minutes)
            origin, dest, t_type = uni["id"], user_stop_id, "dep"
            
        search_time = search_dt.strftime("%H%M")
        params = {
            **STATIC_EFA_PARAMS, 
            "name_origin": origin, 
            "name_destination": dest, 
            "itdDate": t_date, 
            "itdTime": search_time,
            "itdTripDateTimeDepArr": t_type,
            "calcNumberOfTrips": 4
        }
        
        try:
            res = requests.get(BASE_URL, params=params, timeout=10)
            data = res.json()
            results.extend(parse_vvs_data(data))
        except Exception as e:
            print(f"Fehler VVS: {e}")
            continue
    
    if mode == 'to_uni':
        results.sort(key=lambda x: x['arr'], reverse=True)
    else:
        results.sort(key=lambda x: x['dep'])
        
    return jsonify({"journeys": results[:5]})

# - User Preferences -
@app.route('/api/user/profile', methods=['GET', 'POST'])
def manage_profile():
    """
    Verwaltet die benutzerspezifischen Einstellungen (Stundenplan-Link, Heimatstation, Puffer).

    Dieser Endpunkt erlaubt sowohl das Abrufen (GET) als auch das Speichern/Aktualisieren (POST) 
    von Profilinformationen. Die Authentifizierung erfolgt über ein Token, das entweder 
    als Query-Parameter (GET) oder im Authorization-Header (POST) übergeben wird.

    Methoden:
        GET: Ruft das bestehende Profil des authentifizierten Benutzers ab.
        POST: Erstellt ein neues Profil oder aktualisiert ein bestehendes (Upsert-Logik).

    Datenstruktur (JSON POST-Body):
        - course (str): Der Link zum RAPLA-Stundenplan oder die Kursbezeichnung.
        - stop_id (str): Die VVS-ID der Heimat-Haltestelle.
        - stop_name (str): Der Anzeigename der Heimat-Haltestelle.
        - buffer (int): Die bevorzugte Pufferzeit in Minuten.

    Datenbank-Logik:
        Nutzt die 'ON CONFLICT (username) DO UPDATE'-Syntax von PostgreSQL, um 
        Datenredundanz zu vermeiden und Profile effizient zu aktualisieren.

    Returns:
        GET: JSON-Objekt mit den Profildaten oder ein leeres Objekt.
        POST: Status-Meldung {"status": "success"}.

    Status Codes:
        200: Anfrage erfolgreich verarbeitet.
        401: Nicht autorisiert (Token fehlt oder ist ungültig).
    """
    token = request.args.get('token') if request.method == 'GET' else request.headers.get('Authorization')
    username = get_username_from_token(token)
    if not username: return jsonify({"error": "Unauthorized"}), 401
    
    db = get_db_connection()
    # RealDictCursor sorgt dafür, dass die Ergebnisse als Dictionary geliefert werden
    cursor = db.cursor(cursor_factory=RealDictCursor)
    try:
        if request.method == 'GET':
            cursor.execute("SELECT * FROM user_profiles WHERE username = %s", (username,))
            res = cursor.fetchone()
            return jsonify(dict(res) if res else {})
        else:
            d = request.json
            # PostgreSQL "Upsert" Syntax: ON CONFLICT ... DO UPDATE
            sql = """INSERT INTO user_profiles (username, timetable_link, home_stop_id, home_stop_name, buffer_time) 
                     VALUES (%s, %s, %s, %s, %s) 
                     ON CONFLICT (username) DO UPDATE SET 
                     timetable_link=EXCLUDED.timetable_link, 
                     home_stop_id=EXCLUDED.home_stop_id, 
                     home_stop_name=EXCLUDED.home_stop_name, 
                     buffer_time=EXCLUDED.buffer_time"""
            cursor.execute(sql, (username, d.get('course'), d.get('stop_id'), d.get('stop_name'), d.get('buffer')))
            db.commit()
            return jsonify({"status": "success"})
    finally:
        cursor.close()
        db.close()

# - Favoriten -
@app.route('/api/favorites/connection', methods=['POST', 'GET'])
def handle_favorites():
    """
    Verwaltet die gespeicherten Favoritenverbindungen eines Benutzers.

    Ermöglicht das Sichern von spezifischen Fahrtverbindungen in der Datenbank (POST) 
    sowie das Abrufen der persönlichen Favoritenliste (GET). Die Authentifizierung 
    erfolgt via Token-Validierung.

    Methoden:
        POST: Speichert eine neue Verbindung. Erstellt bei Bedarf automatisch 
              einen Eintrag in `user_profiles`, um Fremdschlüssel-Konflikte zu vermeiden.
        GET:  Gibt alle gespeicherten Verbindungen des Nutzers zurück, sortiert nach 
              Erstellungsdatum (neueste zuerst).

    Datenstruktur (JSON POST-Body):
        - dep (str): Abfahrtszeit.
        - arr (str): Ankunftszeit.
        - duration (int): Dauer in Minuten.
        - interchanges (int): Anzahl der Umstiege.
        - sections (list): Liste der Fahrtabschnitte (wird als JSON-String gespeichert).

    Datenbank-Details:
        - Tabelle: `fav_connections`
        - Besonderheit: Das Feld `sections_json` nutzt die Fähigkeit von PostgreSQL, 
          strukturierte Daten (JSON) innerhalb einer Spalte zu speichern.
        - Integrität: Nutzt `ON CONFLICT DO NOTHING`, um sicherzustellen, dass das 
          Nutzerprofil existiert, ohne bestehende Daten zu überschreiben.

    Returns:
        POST: JSON {"status": "success"} bei erfolgreicher Speicherung.
        GET:  JSON-Liste mit allen Favoriten-Einträgen des Benutzers.

    Status Codes:
        200: Erfolg.
        401: Nicht autorisiert (Token ungültig).
    """
    token = request.args.get('token') if request.method == 'GET' else request.headers.get('Authorization')
    username = get_username_from_token(token)
    if not username: return jsonify({"error": "Unauthorized"}), 401

    db = get_db_connection()
    cursor = db.cursor(cursor_factory=RealDictCursor)
    try:
        if request.method == 'POST':
            data = request.json
            # Sicherstellen, dass der User existiert (Postgres Ersatz für INSERT IGNORE)
            cursor.execute("INSERT INTO user_profiles (username) VALUES (%s) ON CONFLICT (username) DO NOTHING", (username,))
            
            sql = """INSERT INTO fav_connections 
                     (username, dep_time, arr_time, duration, interchanges, sections_json) 
                     VALUES (%s, %s, %s, %s, %s, %s)"""
            cursor.execute(sql, (username, data['dep'], data['arr'], data['duration'], 
                                 data['interchanges'], json.dumps(data['sections'])))
            db.commit()
            return jsonify({"status": "success"})
        else:
            cursor.execute("SELECT * FROM fav_connections WHERE username = %s ORDER BY created_at DESC", (username,))
            rows = cursor.fetchall()
            return jsonify([dict(r) for r in rows])
    finally:
        cursor.close()
        db.close()

@app.route('/api/favorites/connection/<int:fav_id>', methods=['DELETE'])
def delete_favorite(fav_id):
    """
    Löscht eine spezifische Favoritenverbindung des authentifizierten Benutzers.

    Die Funktion nutzt die ID des Favoriten-Eintrags und verifiziert zusätzlich 
    den Benutzernamen aus dem Token, um unbefugtes Löschen fremder Einträge zu verhindern.

    Args:
        fav_id (int): Die eindeutige Datenbank-ID des zu löschenden Favoriten. 
                      Wird als Pfad-Parameter in der URL übergeben.

    Authentifizierung:
        Erwartet ein gültiges Token im 'Authorization' Header der Anfrage.

    Datenbank-Sicherheit:
        Das SQL-Statement verwendet eine AND-Bedingung (`id = %s AND username = %s`), 
        sodass der Löschvorgang nur erfolgreich ist, wenn der Eintrag tatsächlich 
        dem anfragenden Benutzer gehört.

    Returns:
        Response: JSON {"status": "deleted"} nach erfolgreicher Ausführung.

    Status Codes:
        200: Erfolgreich gelöscht oder kein entsprechender Eintrag gefunden.
        401: Nicht autorisiert (Token fehlt oder ist ungültig).
    """
    token = request.headers.get('Authorization')
    username = get_username_from_token(token)
    if not username: return jsonify({"error": "Unauthorized"}), 401
    db = get_db_connection()
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM fav_connections WHERE id = %s AND username = %s", (fav_id, username))
        db.commit()
        return jsonify({"status": "deleted"})
    finally:
        cursor.close()
        db.close()

# - Stundenplan -
@app.route('/api/timetable')
def get_timetable():
    """
    Ruft aktuelle Vorlesungsdaten für einen spezifischen Kurs über die dhbw.app API ab.

    Dieser Endpunkt dient als Proxy-Schnittstelle zur Rapla-Anbindung. Er nimmt eine 
    Kursbezeichnung entgegen und leitet die Anfrage an den offiziellen DHBW-API-Service 
    weiter, um aktuelle Event-Daten (Vorlesungen, Prüfungen) zu erhalten.

    Query-Parameter:
        course (str): Die Kursbezeichnung oder der Rapla-Key (z.B. 'STG-TINF23C').

    Funktionsweise:
        1. Validierung: Prüft, ob ein Kurs übergeben wurde.
        2. Proxy-Anfrage: Sendet eine GET-Anfrage an `https://api.dhbw.app/rapla/lectures/{course}/events`.
        3. Fehlerbehandlung: Fängt Timeout- oder Verbindungsfehler zur externen API ab.

    Returns:
        Response: 
            - Bei Erfolg (200): Ein JSON-Array mit den Vorlesungsterminen der dhbw.app.
            - Bei Fehlern (400/500): JSON-Objekt mit entsprechender Fehlermeldung.

    Status Codes:
        200: Erfolgreich Daten von der dhbw.app abgerufen.
        400: Kein Kursname im Query-Parameter angegeben.
        500: Fehler bei der Kommunikation mit der externen DHBW-Schnittstelle.
    """
    course = request.args.get('course')
    if not course: return jsonify({"error": "No course provided"}), 400
    try:
        res = requests.get(f"https://api.dhbw.app/rapla/lectures/{course}/events", timeout=10)
        return jsonify(res.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)