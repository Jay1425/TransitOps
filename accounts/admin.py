from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (
            "TransitOps Information",
            {
                "fields": ("role", "phone"),
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            None,
            {
                "fields": ("role", "phone"),
            },
        ),
    )

    list_display = (
        "username",
        "first_name",
        "last_name",
        "email",
        "role",
        "is_staff",
    )