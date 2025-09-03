"""
Views for handling user authentication and the dashboard.

This module defines function‑based views for sign‑up, login, logout
and displaying a simple dashboard and placeholder pages. The
dashboard and placeholder views are protected so that only logged
in users can access them. On successful registration the user is
redirected to the login page.
"""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from .forms import SignUpForm, LoginForm


def signup_view(request: HttpRequest) -> HttpResponse:
    """Render and process the user registration form."""
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'ثبت‌نام با موفقیت انجام شد. اکنون می‌توانید وارد شوید.')
            return redirect('login')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})


def login_view(request: HttpRequest) -> HttpResponse:
    """Render and process the login form."""
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            # Retrieve the authenticated user from the form's cleaned_data
            user = form.cleaned_data.get('user')
            if user is not None:
                login(request, user)
                return redirect('dashboard')
    else:
        form = LoginForm()
    return render(request, 'registration/login.html', {'form': form})


def logout_view(request: HttpRequest) -> HttpResponse:
    """Log the user out and redirect to the login page."""
    logout(request)
    return redirect('login')


@login_required
def dashboard_view(request: HttpRequest) -> HttpResponse:
    """Display an empty dashboard with only the side menu."""
    return render(request, 'dashboard.html')


@login_required
def page1_view(request: HttpRequest) -> HttpResponse:
    """Placeholder page 1. Content intentionally left blank."""
    return render(request, 'page1.html')


@login_required
def page2_view(request: HttpRequest) -> HttpResponse:
    """Placeholder page 2. Content intentionally left blank."""
    return render(request, 'page2.html')


@login_required
def page3_view(request: HttpRequest) -> HttpResponse:
    """Placeholder page 3. Content intentionally left blank."""
    return render(request, 'page3.html')