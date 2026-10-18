"""B12 docker-stats — tests. Run: pytest test_containerscope.py"""
import sys, os

import pytest
flask_ok = True
try:
    import flask_sqlalchemy
except ImportError:
    flask_ok = False

@pytest.mark.skipif(not flask_ok, reason="flask-sqlalchemy not installed")
def test_series_empty():
    from docker_stats.stats.history import series
    assert series("nonexistent", 60) == []
