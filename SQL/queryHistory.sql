sqlite3 fami.db;
CREATE TABLE account_info (
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT NOT NULL UNIQUE,
nick_name TEXT,
hash TEXT
);