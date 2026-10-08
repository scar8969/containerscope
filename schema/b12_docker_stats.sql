-- 🐳 docker-stats schema
CREATE TABLE snapshots(id INTEGER PRIMARY KEY, container TEXT, cpu REAL DEFAULT 0, mem INTEGER DEFAULT 0, net_in INTEGER DEFAULT 0, net_out INTEGER DEFAULT 0, at DATETIME);
CREATE TABLE alerts(id INTEGER PRIMARY KEY, container TEXT, metric TEXT DEFAULT 'cpu', threshold REAL DEFAULT 90, notify TEXT DEFAULT 'telegram', last_fired DATETIME);
