"""
ASGI config for the Django project.

It exposes the ASGI callable as a module-level variable named
``application``. This allows the project to support asynchronous
servers and protocols such as WebSockets if needed in the future.
"""
from __future__ import annotations

import os

from django.core.asgi import get_asgi_application


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

application = get_asgi_application()