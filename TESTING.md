# PatternGeneratorAPI - Tests

## Running Tests Locally

### Prerequisites
1. Create and activate a Python virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install project dependencies:
```bash
pip install --upgrade pip
pip install -r requirement.txt
```

### Running Tests
Run all tests:
```bash
pytest -v
```

Run specific test file:
```bash
pytest tests/test_db.py -v
pytest tests/test_file_write.py -v
pytest tests/test_api.py -v
```

Run with short output:
```bash
pytest -q
```

## Test Coverage

### Unit Tests (`tests/test_db.py`)
- `test_user_create_authenticate`: User registration and authentication
- `test_file_record_and_touch`: File record creation and TTL extension
- `test_cleanup_expired_files`: Cleanup of expired anonymous files

### File I/O Tests (`tests/test_file_write.py`)
- `test_safe_write_file`: Atomic file write with proper permissions

### API Integration Tests (`tests/test_api.py`)
- `test_register_user`: User registration endpoint
- `test_login_user`: User login endpoint
- `test_login_invalid`: Invalid login credentials rejection
- `test_upload_anonymous`: Anonymous file upload with access_token
- `test_upload_authenticated`: Authenticated file upload
- `test_retrieve_anonymous_invalid_token`: Access control for anonymous files

## CI/CD Pipeline

Tests automatically run on:
- Pull requests targeting `main` branch (via `.github/workflows/ci.yml`)
- Python 3.12, Ubuntu latest
- All tests must pass before PR merge

### GitHub Actions Workflow
Workflow file: `.github/workflows/ci.yml`
- Installs dependencies from `requirement.txt`
- Runs pytest with verbose output
- Uploads test artifacts on failure

## Key Features

✅ **Atomic File Writes**: Tests verify safe_write_file creates files atomically with proper permissions (0o640)

✅ **Database Isolation**: Tests use temporary directories to avoid conflicts

✅ **Anonymous File Access**: Tests verify access_token validation and TTL extension on retrieval

✅ **User Authentication**: Tests cover registration, login, and token-based authorization

✅ **File Cleanup**: Tests verify expired anonymous files are properly deleted

## Debug Mode

For more detailed test output:
```bash
pytest -vv --tb=long
```

To run a single test:
```bash
pytest tests/test_db.py::test_user_create_authenticate -v
```

