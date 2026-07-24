# -*- coding: utf-8 -*-
"""
Пакет tests.test_paths.
"""
import tempfile
import os
from pathlib import Path
from unittest import mock
import sales_assistant.config.paths as paths_mod

def test_ensure_data_dirs_creates_dirs():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Подменяем _DATA_DIR на временную папку
        with mock.patch.object(paths_mod, '_DATA_DIR', Path(tmpdir)):
            with mock.patch.object(paths_mod, 'BACKUPS_DIR', Path(tmpdir) / 'backups'):
                with mock.patch.object(paths_mod, 'CACHE_DIR', Path(tmpdir) / 'cache'):
                    with mock.patch.object(paths_mod, 'IMPORTS_DIR', Path(tmpdir) / 'imports'):
                        with mock.patch.object(paths_mod, 'DOCUMENTS_DIR', Path(tmpdir) / 'documents'):
                            paths_mod.ensure_data_dirs()
                            assert (Path(tmpdir) / 'backups').is_dir()
                            assert (Path(tmpdir) / 'cache').is_dir()