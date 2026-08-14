"""
test_project_structure.py
--------------------------
Sanity checks — confirms all required files and folders exist.
"""

import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def path(*parts): return os.path.join(ROOT, *parts)

class TestProjectStructure:

    def test_core_folders_exist(self):
        for folder in ["app","app/core","app/database","app/services",
                       "app/ml","app/utils","app/pages","database","tests"]:
            assert os.path.isdir(path(folder)), f"Missing folder: {folder}"

    def test_key_files_exist(self):
        for f in [
            "app/main.py",
            "app/core/security.py", "app/core/config.py", "app/core/exceptions.py",
            "app/database/models.py", "app/database/connection.py",
            "app/services/auth_service.py", "app/services/monitoring_service.py",
            "app/services/alert_service.py",
            "app/ml/risk_engine.py",
            "app/pages/1_Login.py", "app/pages/2_Admin_Dashboard.py",
            "app/pages/3_Doctor_Dashboard.py", "app/pages/4_Patient_Dashboard.py",
            "app/utils/custom_css.py",
            "requirements.txt", ".env",
        ]:
            assert os.path.isfile(path(f)), f"Missing file: {f}"

    def test_ml_models_exist(self):
        for model in ["stroke_model.joblib","diabetes_model.joblib","hypertension_model.joblib"]:
            assert os.path.isfile(path("app/ml/trained_models", model)), f"Missing ML model: {model}"

    def test_requirements_not_empty(self):
        req_path = path("requirements.txt")
        with open(req_path) as f:
            content = f.read()
        assert "streamlit" in content
        assert "scikit-learn" in content
        assert "mysql-connector-python" in content

    def test_env_file_has_required_keys(self):
        env_path = path(".env")
        with open(env_path) as f:
            content = f.read()
        for key in ["DB_HOST","DB_NAME","DB_USER","APP_SECRET_KEY"]:
            assert key in content, f"Missing .env key: {key}"
