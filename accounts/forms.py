from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


class LoginForm(AuthenticationForm):
    """Login form with a generic authentication error message."""

    error_messages = {
        "invalid_login": "Invalid username or password.",
        "inactive": "This account is inactive.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"autocomplete": "username"})
        self.fields["password"].widget.attrs.update({"autocomplete": "current-password"})


class SignupForm(UserCreationForm):
    """Signup form using Django's built-in user creation."""

    class Meta:
        model = User
        fields = ("username",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"autocomplete": "username", "class": "form-control"}
        )
        self.fields["password1"].widget.attrs.update(
            {"autocomplete": "new-password", "class": "form-control"}
        )
        self.fields["password2"].widget.attrs.update(
            {"autocomplete": "new-password", "class": "form-control"}
        )
