import sqlite3
from pathlib import Path
from typing import Optional
import hashlib
import uuid
from datetime import datetime, timedelta
import os
import asyncio


DB_PATH = Path('./Data/db.sqlite3')


def _get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    # ensure directory permissions
    try:
        os.chmod(DB_PATH.parent, 0o700)
    except Exception:
        pass
    conn = sqlite3.connect(str(DB_PATH), detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password_hash TEXT,
            role TEXT,
            token TEXT UNIQUE
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY,
            filename TEXT UNIQUE,
            owner_id INTEGER,
            is_anonymous INTEGER,
            created_at TIMESTAMP,
            expires_at TIMESTAMP,
            access_token TEXT UNIQUE
        )
        """
    )
    # ensure access_token column exists for older DBs
    cur.execute("PRAGMA table_info(files)")
    cols = [r[1] for r in cur.fetchall()]
    if 'access_token' not in cols:
        try:
            # SQLite can't add UNIQUE constraint with ALTER TABLE; add simple column then a unique index
            cur.execute("ALTER TABLE files ADD COLUMN access_token TEXT")
            cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_files_access_token ON files(access_token)")
        except Exception:
            pass
    conn.commit()
    conn.close()


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(username: str, password: str, role: str = 'user') -> str:
    token = uuid.uuid4().hex
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, password_hash, role, token) VALUES (?, ?, ?, ?)",
            (username, _hash_password(password), role, token),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise
    conn.close()
    return token


def authenticate_user(username: str, password: str) -> Optional[str]:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    if row and row['password_hash'] == _hash_password(password):
        # return token
        token = row['token']
        conn.close()
        return token
    conn.close()
    return None


def get_user_by_token(token: str) -> Optional[dict]:
    if not token:
        return None
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE token=?", (token,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {"id": row['id'], "username": row['username'], "role": row['role']}


def add_file_record(filename: str, owner_id: Optional[int], is_anonymous: bool, expires_at: Optional[datetime]):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO files (filename, owner_id, is_anonymous, created_at, expires_at, access_token) VALUES (?, ?, ?, ?, ?, ?)",
        (filename, owner_id, int(is_anonymous), datetime.utcnow(), expires_at, None),
    )
    conn.commit()
    conn.close()


def add_file_record_with_token(filename: str, owner_id: Optional[int], is_anonymous: bool, expires_at: Optional[datetime], access_token: Optional[str]):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO files (filename, owner_id, is_anonymous, created_at, expires_at, access_token) VALUES (?, ?, ?, ?, ?, ?)",
        (filename, owner_id, int(is_anonymous), datetime.utcnow(), expires_at, access_token),
    )
    conn.commit()
    conn.close()


def get_file_record(filename: str) -> Optional[dict]:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM files WHERE filename=?", (filename,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return dict(row)


def delete_file_record(filename: str):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM files WHERE filename=?", (filename,))
    conn.commit()
    conn.close()


def delete_file_and_record(filename: str, images_path: str, image_out_path: str):
    p1 = Path(images_path) / filename
    p2 = Path(image_out_path) / filename
    try:
        if p1.exists():
            p1.unlink()
    except Exception:
        pass
    try:
        if p2.exists():
            p2.unlink()
    except Exception:
        pass
    delete_file_record(filename)


def touch_file_record(filename: str, extend_seconds: int):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT expires_at FROM files WHERE filename=?", (filename,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return
    expires = row['expires_at']
    now = datetime.utcnow()
    if expires is None:
        new_expires = now + timedelta(seconds=extend_seconds)
    else:
        # parse if string
        if isinstance(expires, str):
            try:
                expires_dt = datetime.fromisoformat(expires)
            except Exception:
                try:
                    expires_dt = datetime.strptime(expires, '%Y-%m-%d %H:%M:%S.%f')
                except Exception:
                    expires_dt = now
        else:
            expires_dt = expires
        # extend from now
        new_expires = now + timedelta(seconds=extend_seconds)
    cur.execute("UPDATE files SET expires_at=? WHERE filename=?", (new_expires, filename))
    conn.commit()
    conn.close()


def cleanup_expired_files(images_path: str, image_out_path: str):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT filename, expires_at FROM files WHERE is_anonymous=1 AND expires_at IS NOT NULL")
    rows = cur.fetchall()
    now = datetime.utcnow()
    for row in rows:
        expires = row['expires_at']
        if expires is None:
            continue
        # sqlite returns string for timestamp sometimes, try parse
        if isinstance(expires, str):
            try:
                expires_dt = datetime.fromisoformat(expires)
            except Exception:
                try:
                    expires_dt = datetime.strptime(expires, '%Y-%m-%d %H:%M:%S.%f')
                except Exception:
                    continue
        else:
            expires_dt = expires
        if expires_dt <= now:
            delete_file_and_record(row['filename'], images_path, image_out_path)


async def periodic_cleanup(images_path: str, image_out_path: str, interval_seconds: int = 60):
    while True:
        try:
            cleanup_expired_files(images_path, image_out_path)
        except Exception:
            pass
        await asyncio.sleep(interval_seconds)

