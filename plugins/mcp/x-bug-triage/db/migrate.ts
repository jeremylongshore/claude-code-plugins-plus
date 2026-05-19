import { Database } from "bun:sqlite";
import { readFileSync, readdirSync } from "fs";
import { join } from "path";

const DB_PATH = join(import.meta.dir, "..", "data", "triage.db");
const MIGRATIONS_DIR = join(import.meta.dir, "migrations");

export function getDb(path: string = DB_PATH): Database {
  const db = new Database(path, { create: true });
  db.exec("PRAGMA journal_mode = WAL");
  db.exec("PRAGMA foreign_keys = ON");
  return db;
}

export function migrate(db?: Database): void {
  const ownDb = !db;
  db = db ?? getDb();

  try {
    // Ensure schema_version table exists
    db.exec(`
      CREATE TABLE IF NOT EXISTS schema_version (
        version INTEGER PRIMARY KEY,
        applied_at TEXT NOT NULL DEFAULT (datetime('now')),
        description TEXT
      )
    `);

    // Get current version
    const row = db.query("SELECT MAX(version) as v FROM schema_version").get() as { v: number | null } | null;
    const currentVersion = row?.v ?? 0;

    // Find and apply pending migrations
    const files = readdirSync(MIGRATIONS_DIR)
      .filter((f) => f.endsWith(".sql"))
      .sort();

    for (const file of files) {
      const match = file.match(/^(\d+)/);
      if (!match) continue;

      const version = parseInt(match[1], 10);
      if (version <= currentVersion) continue;

      const sql = readFileSync(join(MIGRATIONS_DIR, file), "utf-8");
      db.exec(sql);

      db.query("INSERT INTO schema_version (version, description) VALUES (?, ?)").run(
        version,
        file.replace(/^\d+-/, "").replace(/\.sql$/, "")
      );

      console.log(`Applied migration: ${file}`);
    }

    if (files.length === 0 || currentVersion >= parseInt(files[files.length - 1].match(/^(\d+)/)?.[1] ?? "0", 10)) {
      console.log("Database is up to date.");
    }
  } finally {
    if (ownDb) db.close();
  }
}

// Run migrations if called directly
if (import.meta.main) {
  migrate();
}
