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
-- 2) Fahrten/Verbindungen
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

-- =========================
-- 3) Users: nur externe Identität speichern (kein username/email/passwort)
-- =========================
CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,

  -- Eindeutige ID aus dem Token/Identity-Provider (z.B. "sub" Claim)
  external_user_id VARCHAR(191) NOT NULL,

  -- Wer hat authentifiziert? z.B. "prof-auth", "oauth", "keycloak" ...
  provider VARCHAR(50) NOT NULL DEFAULT 'prof-auth',

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  -- pro Provider darf external_user_id nur einmal vorkommen
  UNIQUE KEY uq_users_provider_external (provider, external_user_id)
);

-- =========================
-- 4) Optional: Sessions/Tokens speichern
-- Empfehlung: NICHT den Klartext-Access-Token speichern,
-- sondern nur einen Hash + Ablaufzeit. (Sicherer bei DB-Leak)
-- =========================
CREATE TABLE IF NOT EXISTS auth_sessions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,

  -- Hash des Access-Tokens (z.B. SHA-256) als Hex-String (64 Zeichen)
  access_token_hash CHAR(64) NOT NULL,

  -- Ablaufzeit laut Token oder vom Auth-Server
  expires_at DATETIME NOT NULL,

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_seen_at DATETIME NULL,

  CONSTRAINT fk_auth_sessions_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,

  UNIQUE KEY uq_access_token_hash (access_token_hash),
  KEY idx_auth_sessions_user (user_id),
  KEY idx_auth_sessions_expires (expires_at)
);

-- =========================
-- 5) Favoriten: bleibt, aber referenziert users
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

  -- verhindert doppelte Favoriten pro User/Stop
  UNIQUE KEY uq_favorites_user_stop (user_id, stop_id)
);

-- =========================
-- 6) Beispiel-Daten
-- =========================
INSERT INTO bus_stops (name, latitude, longitude, vvs_id) VALUES
  ('Haltestelle A - DHBW', 48.7758, 9.1829, 'vvs_001'),
  ('Haltestelle B - Stadtmitte', 48.7758, 9.1829, 'vvs_002'),
  ('Haltestelle C - Bahnhof', 48.7758, 9.1829, 'vvs_003');

INSERT INTO trips (stop_id, departure_time, arrival_time, line_number, destination) VALUES
  (1, '08:00:00', '08:15:00', 'U15', 'Hauptbahnhof'),
  (1, '08:30:00', '08:45:00', 'S6', 'Vaihingen'),
  (2, '09:00:00', '09:20:00', 'U14', 'Degerloch');

-- Optional: Test-User über externe IDs (KEINE Email/Usernames)
INSERT INTO users (provider, external_user_id) VALUES
  ('prof-auth', 'testuser-sub-001'),
  ('prof-auth', 'testuser-sub-002');

-- Optional: Test-Favoriten
INSERT INTO favorites (user_id, stop_id) VALUES
  (1, 1),
  (1, 3),
  (2, 2);

-- =========================
-- 7) Berechtigungen
-- =========================
GRANT ALL PRIVILEGES ON camo_db.* TO 'camo_user'@'%';
FLUSH PRIVILEGES;
