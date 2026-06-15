from pathlib import Path
import uuid


def safe_write_file(dest: Path, content: bytes):
    """Write content atomically to dest and set restrictive permissions."""
    import os
    tmp = dest.parent / f".{dest.name}.{uuid.uuid4().hex}.tmp"
    with open(tmp, "wb") as f:
        f.write(content)
    # atomic replace
    os.replace(tmp, dest)
    try:
        os.chmod(dest, 0o640)
    except Exception:
        pass

