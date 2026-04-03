"""Формы для админки"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    """Форма создания пользователя"""
    username = forms.CharField(required=False)

    class Meta:
        model = CustomUser
        fields = ("username", "email")


class CustomUserChangeForm(UserChangeForm):
    """Форма редактирования пользователя"""
    username = forms.CharField(required=False)

    class Meta:
        model = CustomUser
        fields = ("username", "email")
