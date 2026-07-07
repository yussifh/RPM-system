"""
test_config.py
---------------
Sanity-check test to confirm the project skeleton, imports, and pytest
configuration all work correctly before we build real functionality.
"""

import os
import sys

# Ensure the project root is importable when running pytest from anywhere
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_project_structure_exists():
    """Confirms the core folders exist as expected."""
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    expected_dirs = [
        "app", "app/core", "app/database", "app/services",
        "app/ml", "app/utils", "app/pages", "database", "ml_training",
    ]
    for d in expected_dirs:
        assert os.path.isdir(os.path.join(root, d)), f"Missing expected directory: {d}"
