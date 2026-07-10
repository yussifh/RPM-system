"""
bootstrap_admin.py
--------------------
One-time command-line script to create the FIRST administrator account.

Why this exists: the public registration page only allows patient
self-registration (by design — see auth_service.py). Doctor accounts
are created by an Admin (Phase 8 UI). But the very first Admin account
has to come from somewhere — this script is that entry point, run once
by a developer/deployer directly against the database.

Usage (from the project root, with venv activated and .env configured):
    python scripts/bootstrap_admin.py
"""

import sys
import os
import getpass

# Allow running this script directly via `python scripts/bootstrap_admin.py`
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.auth_service import AuthService
from app.core.exceptions import RPMSystemError


def main() -> None:
    print("=" * 60)
    print(" RPM System — First Administrator Account Setup")
    print("=" * 60)

    full_name = input("Full name: ").strip()
    email = input("Email: ").strip()
    password = getpass.getpass("Password (min 8 chars, 1 letter, 1 number): ")
    confirm = getpass.getpass("Confirm password: ")

    if password != confirm:
        print("\n❌ Passwords do not match. Aborting.")
        sys.exit(1)

    try:
        auth_service = AuthService()
        user = auth_service.register_admin(full_name, email, password)
        print(f"\n✅ Admin account created successfully: {user.full_name} ({user.email})")
        print("You can now log in through the application.")
    except RPMSystemError as e:
        print(f"\n❌ Failed to create admin account: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
