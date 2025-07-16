import os
import shutil
import pytest
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / 'src'))
from utils import archive_existing_file

def test_archive_existing_file(tmp_path):
    # Create a dummy file
    test_file = tmp_path / "testfile.txt"
    test_file.write_text("dummy content")
    # Call archive_existing_file
    archive_existing_file(str(test_file))
    # Check that the file was moved to archive
    archive_dir = tmp_path / "archive"
    archived_files = list(archive_dir.glob("testfile.txt.*"))
    assert len(archived_files) == 1
    assert not test_file.exists()
    # Check that the content is preserved
    assert archived_files[0].read_text() == "dummy content"

def test_archive_existing_file_file_not_exist(tmp_path):
    # Should not raise if file does not exist
    non_existent = tmp_path / "nofile.txt"
    archive_existing_file(str(non_existent))
    # Archive dir should not be created
    assert not (tmp_path / "archive").exists()
