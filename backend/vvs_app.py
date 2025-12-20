import csv
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import base64
import json
import mysql.connector
from dotenv import load_dotenv
import os

app = Flask(__name__)
CORS(app)

load_dotenv()

# --- DATENBANK KONFIGURATION ---
db_config = {
    'host': os.getenv('DB_HOST', 'mariadb'),
    'user': os.getenv('DB_USER', 'camo_user'),
    'password': os.getenv('DB_PASS', 'camo_password123'),
    'database': os.getenv('DB_NAME', 'camo_db'),
    'port': 3306
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

# --- VVS KONFIGURATION ---
BASE_URL = "https://www3.vvs.de/mngvvs/XML_TRIP_REQUEST2"
UNI_STOPS = [
    {"name": "Rosenberg-/Seidenstraße", "id": "de:08111:6072"},
    {"name": "Linden-Museum", "id": "de:08111:2196"}
]

# VOLLSTÄNDIGE PARAMETER (Wichtig für die EFA-Schnittstelle)
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
    "trITArrMOTvalue": 15, 
    "trITDepMOT": 100, 
    "trITDepMOTvalue": 15,
    "type_destination": "any", 
    "type_origin": "any", 
    "useElevationData": 1,
    "useLocalityMainStop": 0, 
    "useRealtime": 1, 
    "useUT": 1, 
    "version": "10.2.10.139"
}

stop_mapping = {}

def load_stops():
    try:
        with open('haltestellen.csv', mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                name, stop_id = row['Name'].strip(), row['Globale ID'].strip()
                zusatz = row.get('Zusatz', '').strip() 
                display_name = f"{name} ({zusatz})" if zusatz else name
                stop_mapping[display_name] = stop_id
    except Exception as e:
        print(f"Fehler CSV: {e}")

load_stops()

# --- HILFSFUNKTIONEN ---

def get_username_from_token(token):
    if not token: return None
    try:
        token_clean = token.split(" ")[1] if " " in token else token
        payload_b64 = token_clean.split('.')[1]
        payload_b64 += '=' * (-len(payload_b64) % 4)
        return json.loads(base64.b64decode(payload_b64).decode('utf-8')).get('sub')
    except: return None

def format_vvs_time(time_str):
    """Extrahiert zuverlässig HH:MM aus VVS-Zeitformaten (ISO oder raw)."""
    if not time_str or not isinstance(time_str, str):
        return "--:--"
    
    # Fall 1: ISO-Format (z.B. 2025-12-20T17:16:00Z)
    if 'T' in time_str:
        try:
            return time_str.split('T')[1][:5]
        except IndexError:
            return "--:--"
    
    # Fall 2: Reines Zahlenformat (z.B. 1716)
    if len(time_str) == 4 and time_str.isdigit():
        return f"{time_str[:2]}:{time_str[2:]}"
        
    return time_str[:5]

def parse_vvs_data(vvs_json):
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

        # --- DAUER-BERECHNUNG (REALE ZEITSPANNE) ---
        # Wir nehmen die exakten Strings, die wir oben für die Anzeige genutzt haben
        first_dep = sections[0]['departure']  # Format "HH:MM"
        last_arr = sections[-1]['arrival']    # Format "HH:MM"
        
        duration_minutes = 0
        
        try:
            # Wir berechnen die Dauer direkt aus den formatierten HH:MM Zeiten
            # Das ist am sichersten, da diese Strings bereits validiert sind
            t1 = datetime.strptime(first_dep, "%H:%M")
            t2 = datetime.strptime(last_arr, "%H:%M")
            
            # Differenz berechnen
            delta = t2 - t1
            seconds = delta.total_seconds()
            
            # Falls die Fahrt über Mitternacht geht (negatives Ergebnis)
            if seconds < 0:
                seconds += 86400 # 24 Stunden dazu addieren
                
            duration_minutes = int(seconds / 60)
            
        except Exception as e:
            # Letzter Fallback: Das duration-Feld der API (Sekunden -> Minuten)
            print(f"Fehler bei Dauer-Berechnung: {e}")
            duration_minutes = journey.get('duration', 0) // 60

        processed.append({
            "dep": first_dep,
            "arr": last_arr,
            "duration": duration_minutes,
            "interchanges": journey.get('interchanges', 0),
            "sections": sections
        })
    return processed

# --- API ROUTEN ---

@app.route('/api/stops')
def get_stops():
    return jsonify([{"name": n, "id": i} for n, i in stop_mapping.items()])

@app.route('/api/connections')
def get_connections():
    mode = request.args.get('mode')
    user_stop_id = request.args.get('userStopId')
    t_date = request.args.get('date') 
    t_time = request.args.get('time')  # Format: "HHMM"
    
    # 1. Puffer aus den Argumenten extrahieren
    try:
        # Wir addieren pauschal 10 Min (Wegzeit) zum User-Puffer
        user_buffer = int(request.args.get('buffer', 0))
        total_buffer_minutes = user_buffer + 10 
    except (ValueError, TypeError):
        total_buffer_minutes = 10

    results = []
    
    # 2. Zeitberechnung vorbereiten
    try:
        base_time = datetime.strptime(t_time, "%H%M")
    except ValueError:
        return jsonify({"error": "Ungültiges Zeitformat"}), 400

    for uni in UNI_STOPS:
        if mode == 'to_uni':
            # HINWEG: Ankunft an der Uni soll sein: Vorlesungsbeginn MINUS Puffer
            search_dt = base_time - timedelta(minutes=total_buffer_minutes)
            origin, dest, t_type = user_stop_id, uni["id"], "arr"
        else:
            # RÜCKWEG: Abfahrt an der Uni soll sein: Vorlesungsende PLUS Puffer
            search_dt = base_time + timedelta(minutes=total_buffer_minutes)
            origin, dest, t_type = uni["id"], user_stop_id, "dep"
            
        # Zeit für VVS-Anfrage formatieren ("HHMM")
        search_time = search_dt.strftime("%H%M")
            
        params = {
            **STATIC_EFA_PARAMS, 
            "name_origin": origin, 
            "name_destination": dest, 
            "itdDate": t_date, 
            "itdTime": search_time,  # Hier wird jetzt die berechnete Zeit genutzt!
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
    
    # Sortierung: Bei Hinfahrt späteste Ankunft zuerst, bei Rückfahrt früheste Abfahrt
    if mode == 'to_uni':
        results.sort(key=lambda x: x['arr'], reverse=True)
    else:
        results.sort(key=lambda x: x['dep'])
        
    return jsonify({"journeys": results[:5]})

@app.route('/api/user/profile', methods=['GET', 'POST'])
def manage_profile():
    token = request.args.get('token') if request.method == 'GET' else request.headers.get('Authorization')
    username = get_username_from_token(token)
    if not username: return jsonify({"error": "Unauthorized"}), 401
    
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        if request.method == 'GET':
            cursor.execute("SELECT * FROM user_profiles WHERE username = %s", (username,))
            return jsonify(cursor.fetchone() or {})
        else:
            d = request.json
            sql = """INSERT INTO user_profiles (username, timetable_link, home_stop_id, home_stop_name, buffer_time) 
                     VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE 
                     timetable_link=VALUES(timetable_link), home_stop_id=VALUES(home_stop_id), 
                     home_stop_name=VALUES(home_stop_name), buffer_time=VALUES(buffer_time)"""
            cursor.execute(sql, (username, d.get('course'), d.get('stop_id'), d.get('stop_name'), d.get('buffer')))
            db.commit()
            return jsonify({"status": "success"})
    finally:
        cursor.close()
        db.close()

@app.route('/api/timetable')
def get_timetable():
    course = request.args.get('course')
    if not course: return jsonify({"error": "No course provided"}), 400
    try:
        res = requests.get(f"https://api.dhbw.app/rapla/lectures/{course}/events", timeout=10)
        return jsonify(res.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/favorites/connection', methods=['POST', 'GET'])
def handle_favorites():
    token = request.args.get('token') if request.method == 'GET' else request.headers.get('Authorization')
    username = get_username_from_token(token)
    if not username: return jsonify({"error": "Unauthorized"}), 401

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        if request.method == 'POST':
            data = request.json
            cursor.execute("INSERT IGNORE INTO user_profiles (username) VALUES (%s)", (username,))
            sql = """INSERT INTO fav_connections 
                     (username, dep_time, arr_time, duration, interchanges, sections_json) 
                     VALUES (%s, %s, %s, %s, %s, %s)"""
            cursor.execute(sql, (username, data['dep'], data['arr'], data['duration'], 
                                 data['interchanges'], json.dumps(data['sections'])))
            db.commit()
            return jsonify({"status": "success"})
        else:
            cursor.execute("SELECT * FROM fav_connections WHERE username = %s ORDER BY created_at DESC", (username,))
            return jsonify(cursor.fetchall())
    finally:
        cursor.close()
        db.close()

@app.route('/api/favorites/connection/<int:fav_id>', methods=['DELETE'])
def delete_favorite(fav_id):
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)