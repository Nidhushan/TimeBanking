from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Skill

User = get_user_model()


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]


class ProfileCreationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["name", "picture", "title", "location", "bio", "link"]


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["name", "picture", "title", "location", "bio", "link"]


class AddSkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ["name"]
        labels = {
            "name": "Skill Name",
        }
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Enter a skill"}),
        }
