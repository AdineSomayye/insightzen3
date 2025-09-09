"""
Forms for handling user registration and login.

These forms encapsulate the fields and validation logic for both
registration (sign‑up) and login. The registration form requires a
strong password as determined by Django's built‑in password
validators. The login form accepts an email and password and relies
on the fact that during registration the email is stored as the
user's username.
"""
from __future__ import annotations

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


class SignUpForm(forms.ModelForm):
    """Custom form for registering a new user.

    The form requests the user's full name, email and password. It
    stores the email both as the username and in the email field and
    places the full name into the first_name attribute for simplicity.
    Password strength is enforced via Django's password validators.
    """

    full_name = forms.CharField(label='نام کامل', max_length=150)
    email = forms.EmailField(label='ایمیل')
    password1 = forms.CharField(label='رمز عبور', widget=forms.PasswordInput)
    password2 = forms.CharField(label='تایید رمز عبور', widget=forms.PasswordInput)

    class Meta:
        model = User
        # We manually specify fields to avoid using Django's default username
        fields: list[str] = []

    def clean_email(self) -> str:
        email = self.cleaned_data.get('email', '').lower().strip()
        if User.objects.filter(username=email).exists():
            raise ValidationError('کاربری با این ایمیل قبلاً ثبت شده است.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'رمزهای عبور مطابقت ندارند.')
        # Validate the password strength using Django's validators
        if password1:
            try:
                validate_password(password1)
            except ValidationError as exc:
                self.add_error('password1', exc)
        return cleaned_data

    def save(self, commit: bool = True) -> User:
        """Create and return a new user instance."""
        email = self.cleaned_data['email'].lower().strip()
        full_name = self.cleaned_data['full_name'].strip()
        password = self.cleaned_data['password1']
        user = User(
            username=email,
            email=email,
            first_name=full_name,
        )
        user.set_password(password)
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    """Simple login form that accepts an email and password."""

    email = forms.EmailField(label='ایمیل')
    password = forms.CharField(label='رمز عبور', widget=forms.PasswordInput)

    def clean(self) -> dict:
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        if email and password:
            # Use the email as username for authentication
            user = authenticate(username=email, password=password)
            if user is None:
                raise ValidationError('اطلاعات ورود نادرست است.')
            cleaned_data['user'] = user
        return cleaned_data