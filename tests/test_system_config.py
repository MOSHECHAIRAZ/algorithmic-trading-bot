import pytest
import json
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / 'src'))
from utils import load_system_config, save_system_config

import os

def test_save_and_load_system_config(tmp_path):
    # Change working directory to tmp_path so system_config.json is created there
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        data = {"foo": 123, "bar": "baz"}
        save_system_config(data)
        loaded = load_system_config()
        assert loaded == data
    finally:
        os.chdir(old_cwd)
