import tempfile
from pathlib import Path
from datetime import timezone
import pytest
from fastapi.testclient import TestClient
import db
from main import app
from input import images_path, image_out_path


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Set DB_PATH to temp directory for test isolation."""
    temp_dir = tmp_path / 'Data'
    temp_dir.mkdir()
    monkeypatch.setattr(db, 'DB_PATH', temp_dir / 'db.sqlite3')
    yield temp_dir


@pytest.fixture(autouse=True)
def setup_dirs(tmp_path, monkeypatch):
    """Setup image directories for tests."""
    img_in = tmp_path / 'images'
    img_out = img_in / 'out'
    img_in.mkdir()
    img_out.mkdir()
    monkeypatch.setattr('input.images_path', str(img_in))
    monkeypatch.setattr('input.image_out_path', str(img_out))
    # also patch in app.py
    import image_processer.app
    monkeypatch.setattr(image_processer.app, 'images_path', str(img_in))
    monkeypatch.setattr(image_processer.app, 'image_out_path', str(img_out))
    yield img_in, img_out


@pytest.fixture
def client():
    """Create test client."""
    # init DB for this test
    db.init_db()
    return TestClient(app)


def test_register_user(client):
    """Test user registration."""
    r = client.post('/users/register', json={'username': 'alice', 'password': 'pw123'})
    assert r.status_code == 200
    data = r.json()
    assert 'token' in data
    token = data['token']
    assert len(token) > 0


def test_login_user(client):
    """Test user login."""
    # register first
    client.post('/users/register', json={'username': 'bob', 'password': 'pw456'})
    # login
    r = client.post('/users/login', json={'username': 'bob', 'password': 'pw456'})
    assert r.status_code == 200
    assert 'token' in r.json()


def test_login_invalid(client):
    """Test login with wrong password."""
    client.post('/users/register', json={'username': 'charlie', 'password': 'pw789'})
    r = client.post('/users/login', json={'username': 'charlie', 'password': 'wrong'})
    assert r.status_code == 401


def test_upload_anonymous(client, tmp_path):
    """Test anonymous upload returns access_token."""
    # create a simple PNG file (minimal valid PNG)
    png_bytes = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D,
        0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
        0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4, 0x89, 0x00, 0x00, 0x00,
        0x0A, 0x49, 0x44, 0x41, 0x54, 0x08, 0x99, 0x01, 0x01, 0x00, 0x00, 0xFE,
        0xFF, 0x00, 0x00, 0x00, 0x02, 0x00, 0x01, 0xE5, 0x21, 0xBC, 0x33, 0x00,
        0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82
    ])
    r = client.post(
        '/image_process/upload_image/',
        files={'file': ('test.png', png_bytes, 'image/png')}
    )
    assert r.status_code == 200
    data = r.json()
    assert data['anonymous'] is True
    assert 'access_token' in data
    assert 'expires_at' in data
    assert data['filename'] == 'test.png'


def test_upload_authenticated(client, tmp_path):
    """Test authenticated user upload (no access_token)."""
    # register and get token
    reg = client.post('/users/register', json={'username': 'dave', 'password': 'pw'})
    user_token = reg.json()['token']

    # create a simple PNG
    png_bytes = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D,
        0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
        0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4, 0x89, 0x00, 0x00, 0x00,
        0x0A, 0x49, 0x44, 0x41, 0x54, 0x08, 0x99, 0x01, 0x01, 0x00, 0x00, 0xFE,
        0xFF, 0x00, 0x00, 0x00, 0x02, 0x00, 0x01, 0xE5, 0x21, 0xBC, 0x33, 0x00,
        0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82
    ])

    # upload as authenticated
    r = client.post(
        '/image_process/upload_image/',
        headers={'Authorization': f'Bearer {user_token}'},
        files={'file': ('test_auth.png', png_bytes, 'image/png')}
    )
    assert r.status_code == 200
    data = r.json()
    assert data['anonymous'] is False
    assert 'access_token' not in data  # should not have access_token for authenticated
    assert data['expires_at'] is None


def test_retrieve_anonymous_invalid_token(client, tmp_path):
    """Test that retrieve without valid token fails."""
    # upload anonymous
    png_bytes = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D,
        0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
        0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4, 0x89, 0x00, 0x00, 0x00,
        0x0A, 0x49, 0x44, 0x41, 0x54, 0x08, 0x99, 0x01, 0x01, 0x00, 0x00, 0xFE,
        0xFF, 0x00, 0x00, 0x00, 0x02, 0x00, 0x01, 0xE5, 0x21, 0xBC, 0x33, 0x00,
        0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82
    ])
    upload_r = client.post(
        '/image_process/upload_image/',
        files={'file': ('out.png', png_bytes, 'image/png')}
    )
    filename = upload_r.json()['filename']

    # try retrieve without token
    get_r = client.get(f'/image_process/get_out_image/{filename}')
    assert get_r.status_code == 404

    # try retrieve with wrong token
    get_r = client.get(f'/image_process/get_out_image/{filename}?access_token=wrongtoken')
    assert get_r.status_code == 404

