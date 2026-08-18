from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from .forms import LoginForm, SignupForm


class UserLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


class UserLogoutView(LogoutView):
    next_page = reverse_lazy("assessment:landing")


def signup(request):
    if request.user.is_authenticated:
        return redirect("assessment:dashboard")

    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Account created successfully. Please log in.",
            )
            return redirect("accounts:login")
    else:
        form = SignupForm()

    return render(request, "accounts/signup.html", {"form": form})
