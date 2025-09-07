import os
import pytest

from app.pdf.layout_utils import load_geometry


def test_load_geometry_success(app):
    with app.app_context():
        repo_root = os.path.abspath(os.path.join(app.root_path, '..'))
        geom = load_geometry('uchiwakesyo_urikakekin', '2025', repo_root=repo_root, required=True, validate=True)
        assert isinstance(geom, dict)
        assert 'row' in geom and 'cols' in geom


def test_load_geometry_missing_year_raises(app):
    with app.app_context():
        repo_root = os.path.abspath(os.path.join(app.root_path, '..'))
        with pytest.raises(FileNotFoundError):
            load_geometry('uchiwakesyo_urikakekin', '1999', repo_root=repo_root, required=True, validate=True)

