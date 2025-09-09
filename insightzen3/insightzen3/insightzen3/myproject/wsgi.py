"""
WSGI config for the Django project.

It exposes the WSGI callable as a module-level variable named
``application``. This is used by Django's development server and
production WSGI servers.
"""
from __future__ import annotations

import os

from django.core.wsgi import get_wsgi_application


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

application = get_wsgi_application()