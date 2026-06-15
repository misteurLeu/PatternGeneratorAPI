import tempfile
from pathlib import Path
import os
import pytest

from image_processer.file_utils import safe_write_file


def test_safe_write_file(tmp_path):
    d = tmp_path / 'upl'
    d.mkdir()
    target = d / 'file.txt'
    content = b'hello world'
    safe_write_file(target, content)
    assert target.exists()
    assert target.read_bytes() == content
    # permissions: owner rw, group r
    mode = target.stat().st_mode & 0o777
    assert mode & 0o600 == 0o600

