# 🐳 CaMo - Docker & MariaDB Setup Guide

## Voraussetzungen

Du brauchst **Docker Desktop** installiert:

### Windows 10/11:
1. Gehe zu https://www.docker.com/products/docker-desktop
2. Lade "Docker Desktop for Windows" herunter
3. Installiere es (Admin-Rechte nötig)
4. Starte deinen Computer neu
5. Öffne PowerShell und tippe: `docker --version`
   - Wenn eine Versionsnummer kommt → Fertig!

-
## Datenbank starten (Schritte für Windows !)

### Schritt 1: Navigiere zum Projektordner
Öffne PowerShell und gehe zum Projekt:

```powershell
cd C:\dev\SoftwareEngineering\CaMo---Campus-Mobility
```

### Schritt 2: Docker Container starten

Gib diesen Befehl ein:

```powershell
docker-compose up -d
```
**Befehle**
- `docker-compose` = "Folge der Anleitung in docker-compose.yml"
- `up` = "Starte die Services"
- `-d` = "Im Hintergrund" (damit die PowerShell frei bleibt)

**Output sollte so aussehen:**
```
Creating network "camo---campus-mobility_camo_network" with driver "bridge"
Creating volume "camo---campus-mobility_mariadb_data" with default driver
Creating camo_database ... done
```

### Schritt 3: Warte 10 Sekunden und prüfe den Status

```powershell
docker-compose ps
```

**Da sollte sowas stehen wie:**
```
NAME              COMMAND             STATUS
camo_database     docker-entrypoint   Up *x* seconds
```

Wenn es "Starting" oder "Restarting" sagt → warte ungeföhr 10 Sekunden und versuch's nochmal!

---

## Testen: Verbindung zur Datenbank

### Mit einem Tool verbinden (DBeaver)

**Probierts mit DBeaver Community Edition (die ist kostenlos:-)** 

1. Lade herunter: https://dbeaver.io/download/
2. Installiere es
3. Öffne DBeaver
4. Klick: `Database` → `New Database Connection`
5. Wähle: `MariaDB`
6. Gib folgende Daten ein:

```
Host: localhost
Port: 3306
Username: camo_user
Password: [Siehe .env.example oder frag jemanden :-)]
Database: camo_db
```

7. Klick `Test Connection` → Sollte sagen: "Connected" 

---

## Datenbank-Struktur

Nach dem Start gibt's  automatisch diese Tabellen:

### 1. `bus_stops` - Haltestellen
```
id | name                      | latitude   | longitude  | vvs_id
1  | Haltestelle A - DHBW     | 48.7758   | 9.1829    | vvs_001
2  | Haltestelle B - Stadtmitte| 48.7758   | 9.1829    | vvs_002
3  | Haltestelle C - Bahnhof  | 48.7758   | 9.1829    | vvs_003
```

### 2. `trips` - Fahrten
```
id | stop_id | departure_time | arrival_time | line_number | destination
1  | 1       | 08:00:00       | 08:15:00     | U15        | Hauptbahnhof
2  | 1       | 08:30:00       | 08:45:00     | S6         | Vaihingen
3  | 2       | 09:00:00       | 09:20:00     | U14        | Degerloch
```

### 3. `users` - Benutzer (für spätere Funktionen)
### 4. `favorites` - Favorisierte Haltestellen

---

## Container stoppen / starten

### Stoppen (Daten bleiben erhalten!):
```powershell
docker-compose down
```

### Wieder starten:
```powershell
docker-compose up -d
```

### Alle Daten löschen (Vorischt: nicht umkehrbar):
```powershell
docker-compose down -v
```

---

## Häufige Probleme & Lösungen

### Problem: "Port 3306 is already in use"
**Lösung:** 
```powershell
# Liste alle Container auf
docker ps -a

# Stoppe den anderen Container
docker stop <container_name>
```

### Problem: "Docker Daemon is not running"
**Lösung:** 
- Öffne Docker Desktop (die Anwendung selbst, nicht nur die CLI)
- Warte bis es vollständig geladen hat

### Problem: "Connection refused"
**Lösung:** 
- Warte noch ein bisschen (Container braucht ~10-20 Sekunden zum Starten)
- Prüfe nochmal: `docker-compose ps`

---

## SQL Befehle (grundlegend)

Mit DBeaver oder der Kommandozeile kannst du die Datenbank abfragen:

### Alle Haltestellen anzeigen:
```sql
SELECT * FROM bus_stops;
```

### Alle Fahrten anzeigen:
```sql
SELECT * FROM trips;
```

### Eine neue Haltestelle hinzufügen:
```sql
INSERT INTO bus_stops (name, latitude, longitude, vvs_id) 
VALUES ('Neue Haltestelle', 48.7758, 9.1829, 'vvs_999');
```

---
## Ihr könnt auch im Terminal arbeiten :-)

docker exec -it camo_database mariadb -u camo_user -p camo_db
-> Passwort eingeben (siehe .env.example) und dann mit SQL rumspielen
Bsp: SELECT * FROM bus_stops;

## Tipps für dein Team

**Damit alle im Team die Datenbank nutzen können:**

1. Der `docker-compose.yml` und `docker/init.sql` müssen ins **Git Repository**
2. Jedes Teammmitglied macht nur:
   ```powershell
   docker-compose up -d
   ```
3. Fertig! Alle haben die gleiche Datenbank mit den gleichen Daten

**Wichtig:** `.env` Dateien mit Passwörtern NICHT ins Git!
(Die `.env.example` zeigt nur welche Variablen es gibt)

---

##  Mehr Infos

- Docker Dokumentation: https://docs.docker.com/
- MariaDB in Docker: https://hub.docker.com/_/mariadb
- Docker Compose: https://docs.docker.com/compose/
