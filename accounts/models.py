from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ("admin", "Administrator"),
        ("fleet_manager", "Fleet Manager"),
        ("dispatcher", "Dispatcher"),
        ("safety_officer", "Safety Officer"),
        ("finance", "Finance Executive"),
    ]

    role = models.CharField(
        max_length=30,
        choices=ROLE_CHOICES,
        default="dispatcher"
    )

    phone = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )

    def __str__(self):
        return self.get_full_name() or self.username