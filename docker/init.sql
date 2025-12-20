USE camo_db;

-- =========================
-- 1) User Profile (Basierend auf 'sub')
-- =========================
CREATE TABLE IF NOT EXISTS user_profiles (
  username VARCHAR(255) PRIMARY KEY, -- Hier speichern wir das 'sub' Feld
  home_stop_id VARCHAR(50) NULL,
  home_stop_name VARCHAR(255) NULL,
  timetable_link VARCHAR(255) NULL,
  buffer_time INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- 2) Favorisierte Haltestellen
-- =========================
CREATE TABLE IF NOT EXISTS fav_stops (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(255) NOT NULL,
  vvs_id VARCHAR(50) NOT NULL,
  stop_name VARCHAR(255) NOT NULL,
  CONSTRAINT fk_fav_stops_user FOREIGN KEY (username) REFERENCES user_profiles(username) ON DELETE CASCADE,
  UNIQUE KEY uq_user_stop (username, vvs_id)
);

-- =========================
-- 3) Favorisierte Verbindungen
-- =========================
CREATE TABLE IF NOT EXISTS fav_connections (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(255) NOT NULL,
  dep_time VARCHAR(10) NOT NULL,     -- z.B. "19:59"
  arr_time VARCHAR(10) NOT NULL,     -- z.B. "20:11"
  duration INT NOT NULL,             -- Minuten
  interchanges INT NOT NULL,
  sections_json JSON NOT NULL,       -- Speichert das komplette Array der Teilstrecken
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_fav_conn_user FOREIGN KEY (username) REFERENCES user_profiles(username) ON DELETE CASCADE
);