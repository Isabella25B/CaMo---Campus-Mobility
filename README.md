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

## Lokal starten:
Perfekte Frage 🙌 — du hast jetzt alles richtig vorbereitet, also können deine Kolleg:innen ganz einfach mitmachen.
Hier kommt die einfache Schritt-für-Schritt-Anleitung, die du ihnen z. B. auch direkt in euer README kopieren kannst 👇
🚀 So starten deine Kolleg:innen das Projekt lokal
🧩 1️⃣ Repository klonen
git clone https://github.com/Isabella25B/CaMo---Campus-Mobility.git
cd CaMo---Campus-Mobility
Wenn du den Soft-UI-Branch noch nicht gemerged hast:
git checkout softui-import
Wenn du schon gemerged hast, bleiben sie einfach auf main.
🐍 2️⃣ Virtuelle Umgebung erstellen
Damit alle die gleichen Pakete nutzen (ohne Systemkonflikte):
macOS / Linux:
python3 -m venv .venv
source .venv/bin/activate
Windows (PowerShell):
py -m venv .venv
.\.venv\Scripts\Activate.ps1
📦 3️⃣ Abhängigkeiten installieren
pip install -r requirements.txt
⚙️ 4️⃣ Datenbank einrichten
python manage.py migrate
👩‍💼 5️⃣ Admin-Benutzer anlegen (nur 1x pro Umgebung)
python manage.py createsuperuser
(z. B. Benutzername: admin, Passwort: admin123)
🚀 6️⃣ Server starten
python manage.py runserver
Dann im Browser öffnen:
👉 http://127.0.0.1:8000/
🔑 7️⃣ Admin-Login (optional)
👉 http://127.0.0.1:8000/admin/
Mit dem eben erstellten Superuser anmelden.
