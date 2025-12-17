import csv
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

BASE_URL = "https://www3.vvs.de/mngvvs/XML_TRIP_REQUEST2"

# Die beiden Uni-Haltestellen als Ziel/Start Anker
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
        # utf-8-sig ignoriert das BOM von Excel-CSVs
        with open('haltestellen.csv', mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                name = row['Name'].strip()
                stop_id = row['Globale ID'].strip()
                # Wir nehmen die vierte Spalte 'Zusatz' für die Anzeige
                zusatz = row.get('Zusatz', '').strip() 
                
                display_name = f"{name} ({zusatz})" if zusatz else name
                stop_mapping[display_name] = stop_id
                
        print(f"✅ CSV geladen: {len(stop_mapping)} Stationen verfügbar.", flush=True)
    except Exception as e:
        print(f"❌ Fehler beim Laden der CSV: {e}", flush=True)

load_stops()

def parse_vvs_data(vvs_json):
    """Extrahiert Reise-Details mit deiner robusten v1 Zeit-Logik."""
    processed = []
    for journey in vvs_json.get('journeys', []):
        legs = journey.get('legs', [])
        if not legs: continue
        
        sections = []
        for leg in legs:
            dep_info = leg.get('origin', {})
            arr_info = leg.get('destination', {})

            dep_raw = leg.get('departureTimeEstimated') or leg.get('departureTimePlanned') or \
                      dep_info.get('departureTimeEstimated') or dep_info.get('departureTimePlanned')
            
            arr_raw = leg.get('arrivalTimeEstimated') or leg.get('arrivalTimePlanned') or \
                      arr_info.get('arrivalTimeEstimated') or arr_info.get('arrivalTimePlanned')

            d_t = dep_raw.split('T')[1][:5] if dep_raw and 'T' in dep_raw else "--:--"
            a_t = arr_raw.split('T')[1][:5] if arr_raw and 'T' in arr_raw else "--:--"
            
            transport = leg.get('transportation', {})
            line = transport.get('disassembledName') or transport.get('number') or "Fussweg"
            
            sections.append({
                "line": line,
                "from": dep_info.get('name', 'Unbekannt'),
                "to": arr_info.get('name', 'Unbekannt'),
                "departure": d_t,
                "arrival": a_t
            })

        processed.append({
            "dep": sections[0]['departure'],
            "arr": sections[-1]['arrival'],
            "duration": sum(l.get('duration', 0) for l in legs) // 60,
            "interchanges": journey.get('interchanges', 0),
            "sections": sections
        })
    return processed

@app.route('/api/stops', methods=['GET'])
def get_stop_list():
    return jsonify([{"name": name, "id": stop_id} for name, stop_id in stop_mapping.items()])

@app.route('/api/connections', methods=['GET'])
def get_connections():
    mode = request.args.get('mode')
    user_stop_id = request.args.get('userStopId') # Eindeutige ID vom Frontend
    target_time = request.args.get('time')
    target_date = request.args.get('date')
    buffer = int(request.args.get('buffer', 0))

    if not user_stop_id:
        return jsonify({"error": "Keine ID übermittelt."}), 400

    combined_results = []

    for uni in UNI_STOPS:
        if mode == 'to_uni':
            time_obj = datetime.strptime(target_time, "%H%M")
            adj_time = (time_obj - timedelta(minutes=buffer)).strftime("%H%M")
            origin, dest, t_type = user_stop_id, uni["id"], "arr"
        else:
            adj_time, origin, dest, t_type = target_time, uni["id"], user_stop_id, "dep"

        params = {**STATIC_EFA_PARAMS, "name_origin": origin, "name_destination": dest, 
                  "itdDate": target_date, "itdTime": adj_time, "itdTripDateTimeDepArr": t_type}

        try:
            res = requests.get(BASE_URL, params=params)
            combined_results.extend(parse_vvs_data(res.json()))
        except: continue

    # Sortieren nach Ankunft (Uni) oder Abfahrt (Heimweg)
    combined_results.sort(key=lambda x: x['arr' if mode == 'to_uni' else 'dep'])
    return jsonify({"journeys": combined_results[:4]})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)