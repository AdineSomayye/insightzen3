"""
URL configuration for the core application.

This module defines the URL patterns for sign‑up, login, logout,
dashboard and a few placeholder pages. Each view is connected to
a named URL so that templates can refer to them easily via the
``url`` template tag.
"""
from __future__ import annotations

from django.urls import path

from . import views


urlpatterns = [
    # Redirect the root URL to the login view so that visiting ``/``
    # shows the login page instead of Django's default placeholder.
    path('', views.login_view, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('page1/', views.page1_view, name='page1'),
    path('page2/', views.page2_view, name='page2'),
    path('page3/', views.page3_view, name='page3'),
    path('coding/', views.coding_view, name='coding'),
    # Route for the new Category functionality
    path('category/', views.category_view, name='category'),
    path('set-language/', views.set_language, name='set_language'),
]