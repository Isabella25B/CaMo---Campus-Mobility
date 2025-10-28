# 🚌 CaMo - Campus Mobility
## 1. Beschreibung

CaMo unterstützt Studierende der DHBW Technik bei einer effizienten und stressfreien An- und Abfahrt. Da sich im Umfeld des Campus zahlreiche Haltestellen befinden, bietet die Anwendung eine Übersicht über alle live Abfahrtszeiten und aktuellen Störungen. So wird ein pünktliches Eintreffen an der Hochschule, als auch eine angenehme Heimreise ermöglicht, ohne unnötige Wartezeiten in Kauf nehmen zu müssen. Die dadurch gewonnene Zeit kann von den Studierenden produktiv für das Studium genutzt werden.

## 2. Funktionale Anforderungen
| ID | Beschreibung | Priorisierung |
| :---: | :--- | :--- |
| 1 | Live ÖPNV-Abfahrtszeiten anzeigen | 🔴 (must have) |
| 2 | Suchen und favorisieren von Verbindungen | 🟠 (should have) |
| 3 | Push-Benachrichtigung bei Verspätungen/Störungen von farvorisierten Fahrten | 🟠 (should have) |
| 4 | Interaktive Karte mit den Haltestellen in der Umgebung, inkl. Wegbeschreibung | 🟡 (could have) |
| 5 | Stundenplan integrieren undautomatisch Verbindungen anzeigen, entsprechend der präferierten Pufferzeit | 🟡 (could have) |
| 6 | Fahrscheine/Tickets kaufen | 🟢 (won't have) |

## 3. Nicht Funktionale Anforderungen
|  | Beschreibung | 
| :---: | :--- |
| 🌐 | öffentliche VVS-Schnittstelle|
| 🗺️ | Open Street Map - OSM |
| 🗓 | Rapla  |
| 💎 | Clean Code |
| 🖊️ | ausführliche Dokumenation |

## 4. MVP - Abgrenzung

Das Minimal Viable Product unserer App bietet Studierenden der DHBW eine Anzeige von Live-Abfahrtszeiten der umliegenden Bus- und Bahnhaltestellen. Dadurch können Nutzer ihre An- und Abfahrt zur Hochschule besser planen, pünktlich ankommen und unnötige Wartezeiten vermeiden.

## 📁 Projektüberblick

- **Framework:** [Django 4.2](https://www.djangoproject.com/)
- **Frontend:** Soft UI Dashboard (Bootstrap 5)
- **Zweck:** Basis-Setup für das Projekt *CaMo – Campus Mobility*
- **Team:** Gruppe DHBW Stuttgart (TINF24B)

---

## ⚙️ Installation & Setup

### 1️⃣ Repository klonen

- git clone https://github.com/Isabella25B/CaMo---Campus-Mobility.git
- cd CaMo---Campus-Mobility 

Wenn der Branch softui-import noch nicht in main gemerged wurde, bitte auf diesen Branch wechseln:
- git checkout softui-import
  
### 2️⃣ Virtuelle Umgebung erstellen
macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
Windows (PowerShell)
py -m venv .venv
.\.venv\Scripts\Activate.ps1

3️⃣ Abhängigkeiten installieren
- pip install -r requirements.txt
4️⃣ Datenbank initialisieren
- python manage.py migrate
5️⃣ Admin-Benutzer erstellen (optional)
- python manage.py createsuperuser
➡️ Damit lässt sich später im Admin-Dashboard anmelden.
6️⃣ Entwicklungsserver starten
- python manage.py runserver  
  
Jetzt kann das Projekt unter
👉 http://127.0.0.1:8000/
im Browser geöffnet werden.  
🔑 Admin-Bereich
URL: http://127.0.0.1:8000/admin/  
Mit dem erstellten Superuser-Account anmelden.
