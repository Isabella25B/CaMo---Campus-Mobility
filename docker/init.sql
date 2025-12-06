-- Datenbank-Initialisierung für CaMo
-- Dieses Script wird automatisch beim Start des Containers ausgeführt

USE camo_db;

-- Tabelle für Haltestellen
CREATE TABLE IF NOT EXISTS bus_stops (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  latitude DECIMAL(10, 8) NOT NULL,
  longitude DECIMAL(11, 8) NOT NULL,
  vvs_id VARCHAR(50) UNIQUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabelle für Fahrten/Verbindungen
CREATE TABLE IF NOT EXISTS trips (
  id INT AUTO_INCREMENT PRIMARY KEY,
  stop_id INT NOT NULL,
  departure_time TIME NOT NULL,
  arrival_time TIME NOT NULL,
  line_number VARCHAR(20) NOT NULL,
  destination VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (stop_id) REFERENCES bus_stops(id)
);

-- Tabelle für Benutzer
CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(100) UNIQUE NOT NULL,
  email VARCHAR(100) UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabelle für Favoriten
CREATE TABLE IF NOT EXISTS favorites (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  stop_id INT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (stop_id) REFERENCES bus_stops(id)
);

-- Beispiel-Daten einfügen
INSERT INTO bus_stops (name, latitude, longitude, vvs_id) VALUES
('Haltestelle A - DHBW', 48.7758, 9.1829, 'vvs_001'),
('Haltestelle B - Stadtmitte', 48.7758, 9.1829, 'vvs_002'),
('Haltestelle C - Bahnhof', 48.7758, 9.1829, 'vvs_003');

INSERT INTO trips (stop_id, departure_time, arrival_time, line_number, destination) VALUES
(1, '08:00:00', '08:15:00', 'U15', 'Hauptbahnhof'),
(1, '08:30:00', '08:45:00', 'S6', 'Vaihingen'),
(2, '09:00:00', '09:20:00', 'U14', 'Degerloch');

INSERT INTO users (username, email) VALUES
('testuser1', 'test1@dhbw.de'),
('testuser2', 'test2@dhbw.de');

-- Berechtigungen sicherstellen
GRANT ALL PRIVILEGES ON camo_db.* TO 'camo_user'@'%';
FLUSH PRIVILEGES;
