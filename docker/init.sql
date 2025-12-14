-- Datenbank-Initialisierung für CaMo
-- Wird automatisch beim Start des Containers ausgeführt

USE camo_db;

-- =========================
-- 1) Haltestellen
-- =========================
CREATE TABLE IF NOT EXISTS bus_stops (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  latitude DECIMAL(10, 8) NOT NULL,
  longitude DECIMAL(11, 8) NOT NULL,
  vvs_id VARCHAR(50) UNIQUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- 2) Fahrten / Verbindungen
-- =========================
CREATE TABLE IF NOT EXISTS trips (
  id INT AUTO_INCREMENT PRIMARY KEY,
  stop_id INT NOT NULL,
  departure_time TIME NOT NULL,
  arrival_time TIME NOT NULL,
  line_number VARCHAR(20) NOT NULL,
  destination VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_trips_stop
    FOREIGN KEY (stop_id) REFERENCES bus_stops(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
);

---------
-- =========================
-- 3) Users: NUR E-Mail + Token
-- =========================
CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,

  -- E-Mail aus dem externen Login (Identifikation)
  email VARCHAR(255) NOT NULL UNIQUE,

  -- Hash des Access-Tokens (z.B. SHA-256)
  access_token_hash CHAR(64) NOT NULL UNIQUE,

  -- Ablaufzeit des Tokens
  token_expires_at DATETIME NOT NULL,

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_seen_at DATETIME NULL
);

-- =========================
-- 4) Favoriten
-- =========================
CREATE TABLE IF NOT EXISTS favorites (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  stop_id INT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT fk_favorites_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,

  CONSTRAINT fk_favorites_stop
    FOREIGN KEY (stop_id) REFERENCES bus_stops(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,

  -- keine doppelten Favoriten
  UNIQUE KEY uq_favorites_user_stop (user_id, stop_id)
);

-- =========================
-- 5) Beispiel-Daten
-- =========================
INSERT INTO bus_stops (name, latitude, longitude, vvs_id) VALUES
  ('Haltestelle A - DHBW', 48.7758, 9.1829, 'vvs_001'),
  ('Haltestelle B - Stadtmitte', 48.7758, 9.1829, 'vvs_002'),
  ('Haltestelle C - Bahnhof', 48.7758, 9.1829, 'vvs_003');

INSERT INTO trips (stop_id, departure_time, arrival_time, line_number, destination) VALUES
  (1, '08:00:00', '08:15:00', 'U15', 'Hauptbahnhof'),
  (1, '08:30:00', '08:45:00', 'S6', 'Vaihingen'),
  (2, '09:00:00', '09:20:00', 'U14', 'Degerloch');

-- Test-User (Token hier nur als Platzhalter!)
INSERT INTO users (email, access_token_hash, token_expires_at) VALUES
  ('test1@dhbw.de', RPAD('a', 64, 'a'), DATE_ADD(NOW(), INTERVAL 1 DAY)),
  ('test2@dhbw.de', RPAD('b', 64, 'b'), DATE_ADD(NOW(), INTERVAL 1 DAY));

INSERT INTO favorites (user_id, stop_id) VALUES
  (1, 1),
  (1, 3),
  (2, 2);

-- =========================
-- 6) Berechtigungen
-- =========================
GRANT ALL PRIVILEGES ON camo_db.* TO 'camo_user'@'%';
FLUSH PRIVILEGES;
