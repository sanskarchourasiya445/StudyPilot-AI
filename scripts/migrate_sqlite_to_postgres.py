"""
StudyPilot AI — SQLite to PostgreSQL Data Migration Script

Safely copies relational records (Users, Resources, Conversations, Messages, Summaries, Notes, Quizzes)
from local SQLite database (studypilot.db) into target PostgreSQL database.
"""

import sys
import os
import sqlite3
import logging
from sqlalchemy import create_engine, text

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("migrate")


def migrate_data():
    sqlite_db_path = os.path.abspath("studypilot.db")
    if not os.path.exists(sqlite_db_path):
        logger.warning(f"SQLite database file not found at {sqlite_db_path}. Skipping data copy.")
        return

    pg_url = settings.DATABASE_URL
    if pg_url.startswith("sqlite"):
        logger.error("DATABASE_URL is set to SQLite. Set DATABASE_URL to PostgreSQL before running migration.")
        return

    logger.info(f"Connecting to source SQLite DB: {sqlite_db_path}")
    sqlite_conn = sqlite3.connect(sqlite_db_path)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cur = sqlite_conn.cursor()

    logger.info(f"Connecting to target PostgreSQL DB: {pg_url}")
    pg_engine = create_engine(pg_url)

    tables = [
        "users",
        "resources",
        "conversations",
        "messages",
        "summaries",
        "notes",
        "quizzes",
    ]

    with pg_engine.connect() as pg_conn:
        transaction = pg_conn.begin()
        try:
            # 1. Migrate users
            sqlite_cur.execute("SELECT * FROM users")
            users = [dict(r) for r in sqlite_cur.fetchall()]
            if users:
                pg_conn.execute(
                    text("INSERT INTO users (id, email, password_hash, name, created_at, updated_at) "
                         "VALUES (:id, :email, :password_hash, :name, :created_at, :updated_at) ON CONFLICT DO NOTHING"),
                    users
                )
            logger.info(f"Migrated {len(users)} users.")

            # Get valid user IDs
            valid_user_ids = set(r[0] for r in pg_conn.execute(text("SELECT id FROM users")).fetchall())

            # 2. Migrate resources
            sqlite_cur.execute("SELECT * FROM resources")
            resources = [dict(r) for r in sqlite_cur.fetchall() if r["user_id"] in valid_user_ids]
            if resources:
                pg_conn.execute(
                    text("INSERT INTO resources (id, user_id, resource_id, source, source_type, title, workspace_id, status, metadata_json, created_at, updated_at) "
                         "VALUES (:id, :user_id, :resource_id, :source, :source_type, :title, :workspace_id, :status, :metadata_json, :created_at, :updated_at) ON CONFLICT DO NOTHING"),
                    resources
                )
            logger.info(f"Migrated {len(resources)} resources.")

            # Get valid resource_ids
            valid_resource_ids = set(r[0] for r in pg_conn.execute(text("SELECT resource_id FROM resources")).fetchall())

            # 3. Migrate conversations
            sqlite_cur.execute("SELECT * FROM conversations")
            raw_convs = [dict(r) for r in sqlite_cur.fetchall() if r["user_id"] in valid_user_ids]
            convs = []
            for c in raw_convs:
                if c["resource_id"] and c["resource_id"] not in valid_resource_ids:
                    c["resource_id"] = None
                convs.append(c)

            if convs:
                pg_conn.execute(
                    text("INSERT INTO conversations (id, user_id, resource_id, title, created_at, updated_at, scope_mode, resource_ids_json) "
                         "VALUES (:id, :user_id, :resource_id, :title, :created_at, :updated_at, :scope_mode, :resource_ids_json) ON CONFLICT DO NOTHING"),
                    convs
                )
            logger.info(f"Migrated {len(convs)} conversations.")

            valid_conv_ids = set(r[0] for r in pg_conn.execute(text("SELECT id FROM conversations")).fetchall())

            # 4. Migrate messages
            sqlite_cur.execute("SELECT * FROM messages")
            messages = [dict(r) for r in sqlite_cur.fetchall() if r["conversation_id"] in valid_conv_ids]
            if messages:
                pg_conn.execute(
                    text("INSERT INTO messages (id, conversation_id, role, content, sources_json, created_at) "
                         "VALUES (:id, :conversation_id, :role, :content, :sources_json, :created_at) ON CONFLICT DO NOTHING"),
                    messages
                )
            logger.info(f"Migrated {len(messages)} messages.")

            # 5. Migrate summaries, notes, quizzes
            for child_table in ["summaries", "notes", "quizzes"]:
                sqlite_cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{child_table}'")
                if not sqlite_cur.fetchone():
                    continue

                sqlite_cur.execute(f"SELECT * FROM {child_table}")
                child_rows = [dict(r) for r in sqlite_cur.fetchall() if r["resource_id"] in valid_resource_ids]
                if child_rows:
                    cols = list(child_rows[0].keys())
                    c_names = ", ".join(cols)
                    p_names = ", ".join([f":{c}" for c in cols])
                    pg_conn.execute(text(f"INSERT INTO {child_table} ({c_names}) VALUES ({p_names}) ON CONFLICT DO NOTHING"), child_rows)
                logger.info(f"Migrated {len(child_rows)} {child_table}.")

            transaction.commit()
            logger.info("Data migration from SQLite to PostgreSQL completed successfully!")
        except Exception as err:
            transaction.rollback()
            logger.error(f"Data migration failed: {err}")
            raise


if __name__ == "__main__":
    migrate_data()
