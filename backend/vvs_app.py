import csv
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import base64
import json
from dotenv import load_dotenv
import os
import psycopg2
from psycopg2.extras import RealDictCursor  # WICHTIG für PostgreSQL Dict-Support

app = Flask(__name__)
CORS(app)

load_dotenv()

# --- DATENBANK KONFIGURATION (PostgreSQL spezifisch) ---
db_config = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASS'),
    'dbname': os.getenv('DB_NAME'),  # psycopg2 nutzt 'dbname' statt 'database'
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

def load_stops():
    try:
        # Pfad eventuell für Docker anpassen, falls die Datei im 'backend' Ordner liegt
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

# --- API ROUTEN ---

@app.route('/api/stops')
def get_stops():
    return jsonify([{"name": n, "id": i} for n, i in stop_mapping.items()])

@app.route('/api/connections')
def get_connections():
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

@app.route('/api/user/profile', methods=['GET', 'POST'])
def manage_profile():
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

@app.route('/api/favorites/connection', methods=['POST', 'GET'])
def handle_favorites():
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

@app.route('/api/timetable')
def get_timetable():
    course = request.args.get('course')
    if not course: return jsonify({"error": "No course provided"}), 400
    try:
        res = requests.get(f"https://api.dhbw.app/rapla/lectures/{course}/events", timeout=10)
        return jsonify(res.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)