from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.mail import send_mail
from transport.utils import check_and_create_notifications
from transport.models import Notification


class Command(BaseCommand):
    help = "Run automated checks for License Expiry, Insurance Expiry, Service Due, and Delayed Trips."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Running TransitOps Automated Reminder & Notification Scanner..."))
        
        new_alerts = check_and_create_notifications()
        self.stdout.write(f"  [SCAN COMPLETED] Generated {new_alerts} new enterprise notifications.")

        # Check if email is configured
        email_host = getattr(settings, "EMAIL_HOST", "")
        if email_host and email_host != "smtp.example.com":
            self.stdout.write(self.style.SUCCESS("  [EMAIL] SMTP configured. Dispatching high-priority alert emails..."))
            unread_errors = Notification.objects.filter(is_read=False, priority="error")[:5]
            for alert in unread_errors:
                try:
                    send_mail(
                        subject=f"[TransitOps Alert] {alert.title}",
                        message=f"{alert.message}\n\nView details: http://127.0.0.1:8000{alert.link}",
                        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "alerts@transitops.erp"),
                        recipient_list=[getattr(settings, "ADMIN_EMAIL", "fleet@transitops.erp")],
                        fail_silently=True,
                    )
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"  [EMAIL ERROR] Could not send email for '{alert.title}': {e}"))
        else:
            self.stdout.write(self.style.WARNING("  [EMAIL NOT CONFIGURED] SMTP settings not active. Reminders are routed directly to the Dashboard Notification Center."))

        self.stdout.write(self.style.SUCCESS("Automated reminders verification finished successfully!"))
