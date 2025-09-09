"""
URL configuration for the Django project.

This module defines the URL patterns that route URLs to views. It
includes the application's URL configuration and the Django admin
interface for completeness, though the admin is not required to run
the sample login/registration flow.
"""
from __future__ import annotations

from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    # Include the core app's URLs at the root of the site
    path('', include('core.urls')),

    # Admin site (optional). You can remove this line if you don't want
    # the admin interface available.
    path('admin/', admin.site.urls),
]