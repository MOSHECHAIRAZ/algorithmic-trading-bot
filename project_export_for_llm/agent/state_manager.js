// state_manager.js (גרסה חדשה ויעילה)
const path = require('path');
// ודא שהספרייה מותקנת: npm install better-sqlite3
const Database = require('better-sqlite3');

const dbPath = path.join(__dirname, 'state.db');
const db = new Database(dbPath);

db.exec(`CREATE TABLE IF NOT EXISTS state (
    key TEXT PRIMARY KEY,
    value TEXT
)`);

const setStateStmt = db.prepare('REPLACE INTO state (key, value) VALUES (?, ?)');
const getStateStmt = db.prepare('SELECT value FROM state WHERE key = ?');

function setState(key, value) {
    return new Promise((resolve) => {
        setStateStmt.run(key, JSON.stringify(value));
        resolve();
    });
}

function getState(key, defaultValue = null) {
    return new Promise((resolve) => {
        const row = getStateStmt.get(key);
        if (row) {
            try {
                resolve(JSON.parse(row.value));
            } catch {
                resolve(defaultValue);
            }
        } else {
            resolve(defaultValue);
        }
    });
}

module.exports = { setState, getState };
