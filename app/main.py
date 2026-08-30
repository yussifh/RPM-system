"""
main.py — App entrypoint / router.

Kept deliberately minimal: role-aware sidebar navigation is built here so
each user only sees the pages they are allowed to access (see
app/core/navigation.py). The actual page content lives under app/pages/.
"""
from app.core.navigation import build_navigation

nav = build_navigation()
nav.run()