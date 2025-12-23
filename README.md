# 🚌🎓 CaMo - Campus Mobility
![Python](https://img.shields.io/badge/Python-3.10-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-2.x-lightgrey?style=flat-square&logo=flask)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14-blue?style=flat-square&logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Enabled-blue?style=flat-square&logo=docker)
![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-yellow?style=flat-square&logo=javascript)

Die Flask-basierte Web-App CaMo unterstützt Studierende der DHBW Technik bei einer effizienten und stressfreien Reise mit dem ÖPNV zwischen dem Campus und der Haustür. Da sich im Umfeld des Technik-Campus mehrere Haltestellen befinden, bietet die Anwendung eine Übersicht über alle live Abfahrtszeiten. Zudem sind mehrere Funktionen zur Fahrtplanung enthalten. So wird ein pünktliches Eintreffen an der Hochschule, als auch eine angenehme Heimreise ermöglicht, ohne unnötige Wartezeiten in Kauf nehmen zu müssen. Die dadurch gewonnene Zeit kann von den Studierenden produktiv für das Studium genutzt werden.

## 1. ✨ Kernfunktionen
* **aktuelle Abfahrtstafel** der beiden Haltestellen `Rosenberg-/Seidenstraße` und `Linden-Museum`
* **Verbindungssuche** mit intelligenter Richtungswahl zwischen „Anfahrt Uni" (Fokus auf Ankunftszeit) und „Rückfahrt Heim“ (Fokus auf Abfahrtszeit) und einkalkulierter Pufferzeit für den Fußweg von der Hochschule zur Haltestelle.
* **Favoriten-System**: personalisierter Speicher für häufig genutzte Verbindungen.
* **Verknüpfung des Vorlesungsplans**: mithilfe der `dhbw.app` Applikation werden die RAPLA Vorlesungspläne ausgelesen und für die nächsten drei Termine An- und Abreise automatisch geladen.
* Integrierte Google Maps **Umgebungskarte** zur schnellen Orientierung und zum Einsehen der Haltestellen rund um den Campus.

## 2. 🚀 Installation & Setup
### Vorraussetzungen
* Docker & Docker Compose
* `.env`-File im Hauptverzeichnis mit Database Credentials (siehe `.env.example`)
### Starten
* Repository klonen
* Container bauen und starten:
```bash
   docker-compose up --build
```

Lokal ist die App unter **http://localhost:9601** erreichbar.
Für das Deployment auf einem Server muss die API-Adresse in der Datei `frontend/config.js` angepasst werden. Ersetze dort die URL durch die entsprechende Domain oder Server-IP, damit das Frontend das Backend im Netzwerk finden kann.

## 3. 🛠 Tech-Stack

* **Frontend**: HTML, CSS, JavaScript
* **Backend**: Flask (Python 3.10), psycopg2 für die Datenbank
* **API**: VVS EFA-Schnittstelle (RapidJSON), RAPLA (Vorlesungsplan)
* **Datenbank**: PostgreSQL
* **Infrastruktur**: Docker & Docker Compose

## 4. Projektstruktur
```
├── .github/workflows      # CI/CD und plantUML workflows
├── docs                   # C4-Modelle
├── backend/
│   ├── vvs_app.py         # Flask Main App
│   ├── requirements.txt   # Python Dependencies
│   └── Dockerfile
│   └── haltestellen.csv   # VVS-Haltestellen mit ID und Teilort 
|                          # (Stand 05.09.2025)
├── frontend/
│   ├── css/               # Stylesheets
│   ├── js/                # Frontend-Logik & API-Calls
│   └── index.html         # Startseite
│   └── Logo.png
│   └── nginx.conf
├── .env
├── docker-compose.yml
└── README.md
```

## 5. ⚠️ Wichtige Hinweise (Known Issues)
> [!IMPORTANT]
> **Education Only:** Dieses Projekt wurde ausschließlich zu Bildungszwecken im Rahmen des Studiums entwickelt.
* **Zeit-Offset**: Aktuell ist bei der Verbindungssuche ein manueller Offset von +1 Stunde implementiert (vvs_app.py line 182), um falsches Zeitverhalten (Zusammenhang mit Winterzeit vermutet) auszugleichen.
* **API-Nutzung**: Die Einbindung der VVS-Schnittstelle erfolgt experimentell. Für eine dauerhafte oder kommerzielle Nutzung der EFA-API ist eine Absprache mit dem Verkehrs- und Tarifverbund Stuttgart (VVS) erforderlich.
