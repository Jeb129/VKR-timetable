from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(required=False)

    class Meta:
        model = CustomUser
        fields = ('username', 'email')

class CustomUserChangeForm(UserChangeForm):
    username = forms.CharField(required=False)

    class Meta:
        model = CustomUser
        fields = ('username', 'email')