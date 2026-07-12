from functools import wraps
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def role_required(*allowed_roles):
    """
    Decorator for views that checks whether the logged-in user has a role
    that is in the allowed_roles list. If not, adds an error message and
    redirects to the dashboard.
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_superuser or request.user.role == "admin" or request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            messages.error(
                request,
                f"Access Denied: Your role ({request.user.get_role_display()}) does not have permission to access this resource."
            )
            return redirect("dashboard")
        return _wrapped_view
    return decorator
