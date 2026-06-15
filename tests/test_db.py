import tempfile
from pathlib import Path
import os
from datetime import timezone
import pytest

import db


@pytest.fixture(autouse=True)
def temp_data_dir(tmp_path, monkeypatch):
    # point DB_PATH to a temp directory for tests
    temp_dir = tmp_path / 'Data'
    temp_dir.mkdir()
    monkeypatch.setattr(db, 'DB_PATH', temp_dir / 'db.sqlite3')
    yield temp_dir


def test_user_create_authenticate():
    db.init_db()
    token = db.create_user('alice', 'pw', 'user')
    assert token
    token2 = db.authenticate_user('alice', 'pw')
    assert token == token2


def test_file_record_and_touch(tmp_path):
    db.init_db()
    fn = 'f1.png'
    access = 'tok123'
    expires = db.datetime.now(timezone.utc).replace(tzinfo=None) + db.timedelta(seconds=3600)
    db.add_file_record_with_token(fn, None, True, expires, access)
    rec = db.get_file_record(fn)
    assert rec['filename'] == fn
    assert rec['access_token'] == access
    # touch should extend expiry to ~now+3600
    old = rec['expires_at']
    db.touch_file_record(fn, 3600)
    rec2 = db.get_file_record(fn)
    assert rec2['expires_at'] is not None
    assert rec2['expires_at'] != old


def test_cleanup_expired_files(tmp_path, monkeypatch):
    # setup images dirs
    images_in = tmp_path / 'images'
    images_out = images_in / 'out'
    images_in.mkdir()
    images_out.mkdir()
    # init DB in Data
    db.init_db()
    fn = 'to_delete.png'
    access = 'tokdel'
    # create dummy files
    f_in = images_in / fn
    f_out = images_out / fn
    f_in.write_bytes(b'123')
    f_out.write_bytes(b'456')
    # insert expired record
    expired = db.datetime(2000, 1, 1)
    db.add_file_record_with_token(fn, None, True, expired, access)
    # run cleanup
    db.cleanup_expired_files(str(images_in), str(images_out))
    assert not f_in.exists()
    assert not f_out.exists()
    assert db.get_file_record(fn) is None

