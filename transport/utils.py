import datetime
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import Vehicle, Driver, Maintenance, Trip, FuelLog, Expense, VehicleDocument, Notification


def check_and_create_notifications():
    """
    Scans ERP database entities and generates enterprise notifications & alerts.
    """
    today = timezone.now().date()
    now = timezone.now()
    created_count = 0

    # 1. Check Driver License Expiry (within 30 days or expired)
    drivers = Driver.objects.filter(is_active=True)
    for d in drivers:
        if not d.license_expiry:
            continue
        days = (d.license_expiry - today).days
        if days <= 30:
            title = f"License Expiry Alert: {d.name}"
            msg = f"Driver {d.name} ({d.license_number}) license expires in {days} days on {d.license_expiry}."
            if days < 0:
                title = f"CRITICAL: License Expired ({d.name})"
                msg = f"Driver {d.name} ({d.license_number}) license EXPIRED by {abs(days)} days!"
            
            # Prevent duplicate unread notifications
            if not Notification.objects.filter(notification_type="license_expiry", title=title, is_read=False).exists():
                Notification.objects.create(
                    notification_type="license_expiry",
                    title=title,
                    message=msg,
                    priority="error" if days <= 7 else "warning",
                    link=f"/drivers/{d.pk}/edit/"
                )
                created_count += 1

    # 2. Check Vehicle Insurance / Documents Expiry
    vehicles = Vehicle.objects.filter(is_active=True)
    for v in vehicles:
        if v.insurance_expiry:
            days = (v.insurance_expiry - today).days
            if days <= 30:
                title = f"Insurance Expiry Alert: {v.registration_number}"
                msg = f"Vehicle {v.registration_number} ({v.vehicle_name}) insurance expires in {days} days on {v.insurance_expiry}."
                if not Notification.objects.filter(notification_type="insurance_expiry", title=title, is_read=False).exists():
                    Notification.objects.create(
                        notification_type="insurance_expiry",
                        title=title,
                        message=msg,
                        priority="error" if days <= 7 else "warning",
                        link=f"/fleet/{v.pk}/"
                    )
                    created_count += 1

    # Also check VehicleDocuments
    docs = VehicleDocument.objects.filter(is_active=True)
    for doc in docs:
        if doc.expiry_date:
            days = (doc.expiry_date - today).days
            if days <= 30:
                title = f"Document Expiry: {doc.vehicle.registration_number} ({doc.get_doc_type_display()})"
                msg = f"{doc.get_doc_type_display()} #{doc.document_number} for {doc.vehicle.registration_number} expires in {days} days."
                if not Notification.objects.filter(title=title, is_read=False).exists():
                    Notification.objects.create(
                        notification_type="insurance_expiry" if doc.doc_type == "insurance" else "service_due",
                        title=title,
                        message=msg,
                        priority="error" if days <= 7 else "warning",
                        link=f"/fleet/{doc.vehicle.pk}/"
                    )
                    created_count += 1

    # 3. Check Scheduled Service Due
    maints = Maintenance.objects.filter(is_active=True, status="scheduled")
    for m in maints:
        days = (m.scheduled_date - today).days
        if days <= 7:
            title = f"Service Due: {m.vehicle.registration_number} ({m.service_type})"
            msg = f"Scheduled maintenance for {m.vehicle.registration_number} is due in {days} days on {m.scheduled_date} at {m.technician}."
            if not Notification.objects.filter(notification_type="service_due", title=title, is_read=False).exists():
                Notification.objects.create(
                    notification_type="service_due",
                    title=title,
                    message=msg,
                    priority="warning" if days > 1 else "error",
                    link=f"/maintenance/{m.pk}/"
                )
                created_count += 1

    # 4. Check Delayed Trips
    active_trips = Trip.objects.filter(is_active=True, status="dispatched", arrival_time__isnull=False)
    for t in active_trips:
        if t.arrival_time and t.arrival_time < now:
            hours_delay = round((now - t.arrival_time).total_seconds() / 3600, 1)
            title = f"Trip Delayed: {t.trip_number}"
            msg = f"Dispatch {t.trip_number} ({t.pickup} -> {t.destination}) by Driver {t.driver.name} is overdue by {hours_delay} hours."
            if not Notification.objects.filter(notification_type="trip_delayed", title=title, is_read=False).exists():
                Notification.objects.create(
                    notification_type="trip_delayed",
                    title=title,
                    message=msg,
                    priority="error",
                    link=f"/trips/{t.pk}/edit/"
                )
                created_count += 1

    return created_count
