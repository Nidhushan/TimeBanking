from django.contrib.auth.forms import UserCreationForm
from .models import User
from django import forms
from django.contrib.auth import get_user_model
from .models import Feedback

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


class FeedbackForm(forms.ModelForm):
    rating = forms.IntegerField(min_value=1, max_value=5, label='Rating (1-5)')
    comment = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), required=False)

    class Meta:
        model = Feedback
        fields = ['rating', 'comment']