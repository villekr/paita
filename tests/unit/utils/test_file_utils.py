import contextlib
import os
import shutil
import tempfile
from pathlib import Path

import pytest

from paita.utils import file_utils


@pytest.fixture
def folder():
    folder_path = tempfile.mkdtemp()
    with open(os.path.join(folder_path, "file1.txt"), "wb") as f:
        f.write(b"Hello")
    with open(os.path.join(folder_path, "file2.txt"), "wb") as f:
        f.write(b"World")

    yield folder_path
    with contextlib.suppress(FileNotFoundError):
        shutil.rmtree(folder_path)


@pytest.mark.asyncio
async def test_delete_folder(folder):
    await file_utils.delete_folder(Path(folder), recursive=True, dry_run=False)
    with pytest.raises(FileNotFoundError):
        shutil.rmtree(folder)
