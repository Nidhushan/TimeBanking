from django.contrib.auth.forms import UserCreationForm
from .models import User
from django import forms

class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

class ProfileCreationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["name", "picture", "title", "location", "bio", "link"]