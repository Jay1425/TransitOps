from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.utils.http import url_has_allowed_host_and_scheme
from .forms import LoginForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    form = LoginForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]
        remember_me = form.cleaned_data["remember_me"]

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            if user.is_active:
                login(request, user)

                if not remember_me:
                    request.session.set_expiry(0)
                else:
                    request.session.set_expiry(1209600)  # 2 weeks

                messages.success(
                    request,
                    f"Welcome back, {user.get_full_name() or user.username} ({user.get_role_display()})!"
                )

                next_url = request.GET.get("next")
                if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                    return redirect(next_url)

                return redirect("dashboard")
            else:
                messages.error(request, "Your account has been disabled. Please contact the administrator.")
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out of TransitOps ERP successfully.")
    return redirect("login")