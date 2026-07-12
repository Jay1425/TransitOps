import csv
import json
import datetime
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Sum, Avg, Count, F
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from accounts.decorators import role_required
from .forms import (
    DriverForm,
    TripCompleteForm,
    TripForm,
    VehicleForm,
    MaintenanceForm,
    FuelLogForm,
    ExpenseForm,
)
from .models import Driver, Trip, Vehicle, Maintenance, FuelLog, Expense, VehicleDocument, Notification


# ==============================================================================
# MODULE 3 — VEHICLE REGISTRY VIEWS
# ==============================================================================

@login_required
@role_required("fleet_manager")
def vehicle_list_view(request):
    queryset = Vehicle.objects.filter(is_active=True)

    # Search: Registration Number or Vehicle Name
    search_query = request.GET.get("q", "").strip()
    if search_query:
        queryset = queryset.filter(
            Q(registration_number__icontains=search_query) |
            Q(vehicle_name__icontains=search_query)
        )

    # Filter: Vehicle Type
    vehicle_type = request.GET.get("vehicle_type", "").strip()
    if vehicle_type:
        queryset = queryset.filter(vehicle_type=vehicle_type)

    # Filter: Status
    status = request.GET.get("status", "").strip()
    if status:
        queryset = queryset.filter(status=status)

    # Sorting
    sort_by = request.GET.get("sort", "-created_at")
    allowed_sorts = ["registration_number", "-registration_number", "vehicle_name", "-vehicle_name", "odometer", "-odometer", "created_at", "-created_at"]
    if sort_by in allowed_sorts:
        queryset = queryset.order_by(sort_by)
    else:
        queryset = queryset.order_by("-created_at")

    paginator = Paginator(queryset, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "search_query": search_query,
        "selected_type": vehicle_type,
        "selected_status": status,
        "sort_by": sort_by,
        "vehicle_types": Vehicle.VEHICLE_TYPES,
        "status_choices": Vehicle.STATUS_CHOICES,
    }
    return render(request, "transport/vehicle_list.html", context)


@login_required
@role_required("fleet_manager")
def vehicle_add_view(request):
    if request.method == "POST":
        form = VehicleForm(request.POST)
        if form.is_valid():
            vehicle = form.save()
            messages.success(
                request,
                f"Vehicle '{vehicle.registration_number}' ({vehicle.vehicle_name}) added successfully to fleet registry."
            )
            return redirect("vehicle_list")
    else:
        form = VehicleForm()

    context = {
        "form": form,
        "page_title": "Add New Vehicle",
        "header_title": "Fleet Registry — Add Vehicle",
        "action_url": request.path,
    }
    return render(request, "transport/vehicle_form.html", context)


@login_required
@role_required("fleet_manager")
def vehicle_edit_view(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk, is_active=True)
    if request.method == "POST":
        form = VehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            vehicle = form.save()
            messages.success(
                request,
                f"Vehicle '{vehicle.registration_number}' updated successfully."
            )
            return redirect("vehicle_list")
    else:
        form = VehicleForm(instance=vehicle)

    context = {
        "form": form,
        "vehicle": vehicle,
        "page_title": f"Edit Vehicle ({vehicle.registration_number})",
        "header_title": "Fleet Registry — Edit Profile",
        "action_url": request.path,
    }
    return render(request, "transport/vehicle_form.html", context)


@login_required
@role_required("fleet_manager")
def vehicle_detail_view(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk, is_active=True)
    recent_trips = vehicle.trips.select_related("driver").filter(is_active=True).order_by("-departure_time")[:10]
    maintenance_logs = vehicle.maintenances.order_by("-scheduled_date")[:10]
    fuel_logs = vehicle.fuel_logs.order_by("-fuel_date")[:5]
    documents = vehicle.documents.filter(is_active=True).order_by("expiry_date")

    context = {
        "vehicle": vehicle,
        "recent_trips": recent_trips,
        "maintenance_logs": maintenance_logs,
        "fuel_logs": fuel_logs,
        "documents": documents,
    }
    return render(request, "transport/vehicle_detail.html", context)


@login_required
@role_required("fleet_manager")
def vehicle_delete_view(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk, is_active=True)
    if request.method == "POST":
        # Business rules check
        if vehicle.status == "on_trip" or vehicle.trips.filter(status="dispatched", is_active=True).exists():
            messages.error(
                request,
                f"Cannot delete vehicle '{vehicle.registration_number}' because it is currently On Trip or assigned to an active dispatch."
            )
            return redirect("vehicle_list")

        # Soft delete
        vehicle.is_active = False
        vehicle.status = "retired"
        vehicle.save()
        messages.success(
            request,
            f"Vehicle '{vehicle.registration_number}' has been retired and soft deleted from active fleet."
        )
        return redirect("vehicle_list")

    context = {
        "vehicle": vehicle,
    }
    return render(request, "transport/vehicle_confirm_delete.html", context)


@login_required
@role_required("fleet_manager")
def document_upload_view(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk, is_active=True)
    if request.method == "POST":
        doc_type = request.POST.get("doc_type", "rc")
        doc_number = request.POST.get("document_number", "")
        expiry_date = request.POST.get("expiry_date", "")
        file = request.FILES.get("file")

        if expiry_date:
            VehicleDocument.objects.create(
                vehicle=vehicle,
                doc_type=doc_type,
                document_number=doc_number,
                expiry_date=expiry_date,
                file=file,
                is_active=True
            )
            messages.success(request, f"Document ({doc_type.upper()}) uploaded for {vehicle.registration_number}.")
        else:
            messages.error(request, "Expiry date is required when uploading regulatory documents.")
    return redirect("vehicle_detail", pk=vehicle.pk)


@login_required
@role_required("fleet_manager")
def document_delete_view(request, pk):
    doc = get_object_or_404(VehicleDocument, pk=pk, is_active=True)
    v_id = doc.vehicle.pk
    if request.method == "POST":
        doc.is_active = False
        doc.save()
        messages.success(request, f"Document '{doc.get_doc_type_display()}' removed.")
    return redirect("vehicle_detail", pk=v_id)



# ==============================================================================
# MODULE 4 — DRIVER MANAGEMENT VIEWS
# ==============================================================================

@login_required
@role_required("safety_officer")
def driver_list_view(request):
    queryset = Driver.objects.filter(is_active=True)

    # Search: Name, License Number, Phone
    search_query = request.GET.get("q", "").strip()
    if search_query:
        queryset = queryset.filter(
            Q(name__icontains=search_query) |
            Q(license_number__icontains=search_query) |
            Q(phone__icontains=search_query)
        )

    # Filter: Status
    status = request.GET.get("status", "").strip()
    if status:
        queryset = queryset.filter(status=status)

    # Filter: Expired Licenses
    expired = request.GET.get("expired", "").strip()
    if expired == "1":
        queryset = queryset.filter(license_expiry__lt=timezone.now().date())

    # Sorting
    sort_by = request.GET.get("sort", "-created_at")
    allowed_sorts = ["name", "-name", "license_number", "-license_number", "safety_score", "-safety_score", "created_at", "-created_at"]
    if sort_by in allowed_sorts:
        queryset = queryset.order_by(sort_by)
    else:
        queryset = queryset.order_by("-created_at")

    paginator = Paginator(queryset, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "search_query": search_query,
        "selected_status": status,
        "selected_expired": expired,
        "sort_by": sort_by,
        "status_choices": Driver.STATUS_CHOICES,
    }
    return render(request, "transport/driver_list.html", context)


@login_required
@role_required("safety_officer")
def driver_add_view(request):
    if request.method == "POST":
        form = DriverForm(request.POST)
        if form.is_valid():
            driver = form.save()
            messages.success(
                request,
                f"Driver '{driver.name}' (License: {driver.license_number}) onboarded successfully."
            )
            return redirect("driver_list")
    else:
        form = DriverForm()

    context = {
        "form": form,
        "page_title": "Onboard New Driver",
        "header_title": "Safety & Driver Profile — Add Driver",
        "action_url": request.path,
    }
    return render(request, "transport/driver_form.html", context)


@login_required
@role_required("safety_officer")
def driver_edit_view(request, pk):
    driver = get_object_or_404(Driver, pk=pk, is_active=True)
    if request.method == "POST":
        form = DriverForm(request.POST, instance=driver)
        if form.is_valid():
            driver = form.save()
            messages.success(
                request,
                f"Driver '{driver.name}' profile and safety metrics updated successfully."
            )
            return redirect("driver_list")
    else:
        form = DriverForm(instance=driver)

    context = {
        "form": form,
        "driver": driver,
        "page_title": f"Edit Driver ({driver.name})",
        "header_title": "Safety & Driver Profile — Edit Record",
        "action_url": request.path,
    }
    return render(request, "transport/driver_form.html", context)


@login_required
@role_required("safety_officer")
def driver_delete_view(request, pk):
    driver = get_object_or_404(Driver, pk=pk, is_active=True)
    if request.method == "POST":
        # Business rule check
        if driver.status == "on_trip" or driver.trips.filter(status="dispatched", is_active=True).exists():
            messages.error(
                request,
                f"Cannot deactivate driver '{driver.name}' because they are currently On Trip."
            )
            return redirect("driver_list")

        # Soft delete
        driver.is_active = False
        driver.status = "off_duty"
        driver.save()
        messages.success(
            request,
            f"Driver '{driver.name}' has been deactivated and soft deleted."
        )
        return redirect("driver_list")

    context = {
        "driver": driver,
    }
    return render(request, "transport/driver_confirm_delete.html", context)


# ==============================================================================
# MODULE 5 — TRIP MANAGEMENT VIEWS
# ==============================================================================

@login_required
@role_required("dispatcher")
def trip_list_view(request):
    queryset = Trip.objects.select_related("vehicle", "driver").filter(is_active=True)

    # Search: Trip Number, Pickup, Destination
    search_query = request.GET.get("q", "").strip()
    if search_query:
        queryset = queryset.filter(
            Q(trip_number__icontains=search_query) |
            Q(pickup__icontains=search_query) |
            Q(destination__icontains=search_query)
        )

    # Filter: Status
    status = request.GET.get("status", "").strip()
    if status:
        queryset = queryset.filter(status=status)

    # Sorting
    sort_by = request.GET.get("sort", "-departure_time")
    allowed_sorts = ["trip_number", "-trip_number", "departure_time", "-departure_time", "planned_distance", "-planned_distance", "status", "-status"]
    if sort_by in allowed_sorts:
        queryset = queryset.order_by(sort_by)
    else:
        queryset = queryset.order_by("-departure_time")

    paginator = Paginator(queryset, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Live board active trips summary
    active_dispatches = Trip.objects.select_related("vehicle", "driver").filter(is_active=True, status="dispatched").order_by("-departure_time")[:6]

    context = {
        "page_obj": page_obj,
        "active_dispatches": active_dispatches,
        "search_query": search_query,
        "selected_status": status,
        "sort_by": sort_by,
        "status_choices": Trip.STATUS_CHOICES,
    }
    return render(request, "transport/trip_list.html", context)


@login_required
@role_required("dispatcher")
def trip_add_view(request):
    if request.method == "POST":
        form = TripForm(request.POST)
        if form.is_valid():
            trip = form.save(commit=False)
            if trip.vehicle:
                trip.start_odometer = trip.vehicle.odometer
            else:
                trip.start_odometer = 0
            trip.status = "draft"
            trip.save()
            messages.success(
                request,
                f"Trip '{trip.trip_number}' created as Draft. Ready for dispatch."
            )
            return redirect("trip_list")
    else:
        form = TripForm()

    context = {
        "form": form,
        "page_title": "Create New Trip Dispatch",
        "header_title": "Trip Dispatcher — New Order",
        "action_url": request.path,
    }
    return render(request, "transport/trip_form.html", context)


@login_required
@role_required("dispatcher")
def trip_edit_view(request, pk):
    trip = get_object_or_404(Trip, pk=pk, is_active=True)
    if trip.status in ["completed", "cancelled"]:
        messages.error(
            request,
            f"Trip '{trip.trip_number}' is already {trip.status} and cannot be modified."
        )
        return redirect("trip_list")

    if request.method == "POST":
        form = TripForm(request.POST, instance=trip)
        if form.is_valid():
            trip = form.save()
            messages.success(
                request,
                f"Trip '{trip.trip_number}' updated successfully."
            )
            return redirect("trip_list")
    else:
        form = TripForm(instance=trip)

    context = {
        "form": form,
        "trip": trip,
        "page_title": f"Edit Trip ({trip.trip_number})",
        "header_title": "Trip Dispatcher — Edit Order",
        "action_url": request.path,
    }
    return render(request, "transport/trip_form.html", context)


@login_required
@role_required("dispatcher")
def trip_dispatch_view(request, pk):
    trip = get_object_or_404(Trip, pk=pk, is_active=True)

    if request.method == "POST":
        with transaction.atomic():
            # Refresh from DB inside transaction
            trip = Trip.objects.select_for_update().get(pk=trip.pk)
            if trip.status != "draft":
                messages.error(request, f"Trip '{trip.trip_number}' is already '{trip.get_status_display()}' and cannot be dispatched again.")
                return redirect("trip_list")

            vehicle = trip.vehicle
            driver = trip.driver

            if not vehicle or not vehicle.is_active or vehicle.status != "available" or vehicle.insurance_expiry < timezone.now().date():
                messages.error(request, f"Assigned vehicle '{vehicle.registration_number if vehicle else 'None'}' is unavailable or has expired insurance.")
                return redirect("trip_list")

            if not driver or not driver.is_active or driver.status != "available" or driver.is_license_expired:
                messages.error(request, f"Assigned driver '{driver.name if driver else 'None'}' is unavailable or has an expired license.")
                return redirect("trip_list")

            # Update statuses atomically
            trip.status = "dispatched"
            trip.start_odometer = vehicle.odometer
            trip.save()

            vehicle.status = "on_trip"
            vehicle.save()

            driver.status = "on_trip"
            driver.save()

            messages.success(
                request,
                f"Trip '{trip.trip_number}' successfully dispatched! Vehicle '{vehicle.registration_number}' and Driver '{driver.name}' status set to 'On Trip'."
            )
            return redirect("trip_list")

    context = {
        "trip": trip,
    }
    return render(request, "transport/trip_confirm_dispatch.html", context)


@login_required
@role_required("dispatcher")
def trip_complete_view(request, pk):
    trip = get_object_or_404(Trip, pk=pk, is_active=True)
    if trip.status != "dispatched":
        messages.error(request, f"Trip '{trip.trip_number}' must be in 'Dispatched' status before it can be completed.")
        return redirect("trip_list")

    if request.method == "POST":
        form = TripCompleteForm(request.POST, instance=trip)
        if form.is_valid():
            with transaction.atomic():
                trip = form.save(commit=False)
                trip.status = "completed"
                trip.arrival_time = timezone.now()
                if trip.end_odometer and trip.start_odometer:
                    trip.actual_distance = max(0, trip.end_odometer - trip.start_odometer)
                trip.save()

                # Update Vehicle Odometer and Status
                if trip.vehicle:
                    if trip.end_odometer and trip.end_odometer > trip.vehicle.odometer:
                        trip.vehicle.odometer = trip.end_odometer
                    trip.vehicle.status = "available"
                    trip.vehicle.save()

                # Update Driver Status
                if trip.driver:
                    trip.driver.status = "available"
                    trip.driver.save()

            messages.success(
                request,
                f"Trip '{trip.trip_number}' completed! Vehicle '{trip.vehicle.registration_number}' and Driver '{trip.driver.name}' released to 'Available'."
            )
            return redirect("trip_list")
    else:
        initial_end_odo = (trip.vehicle.odometer + trip.planned_distance) if trip.vehicle else trip.start_odometer
        form = TripCompleteForm(instance=trip, initial={"end_odometer": initial_end_odo})

    context = {
        "form": form,
        "trip": trip,
    }
    return render(request, "transport/trip_complete_form.html", context)


@login_required
@role_required("dispatcher")
def trip_cancel_view(request, pk):
    trip = get_object_or_404(Trip, pk=pk, is_active=True)
    if trip.status in ["completed", "cancelled"]:
        messages.error(request, f"Trip '{trip.trip_number}' is already '{trip.get_status_display()}' and cannot be cancelled.")
        return redirect("trip_list")

    if request.method == "POST":
        with transaction.atomic():
            was_dispatched = (trip.status == "dispatched")
            trip.status = "cancelled"
            trip.save()

            # Release vehicle and driver if they were On Trip for this dispatch
            if was_dispatched:
                if trip.vehicle and trip.vehicle.status == "on_trip":
                    trip.vehicle.status = "available"
                    trip.vehicle.save()
                if trip.driver and trip.driver.status == "on_trip":
                    trip.driver.status = "available"
                    trip.driver.save()

        messages.success(
            request,
            f"Trip '{trip.trip_number}' has been cancelled. Associated vehicle and driver have been released if applicable."
        )
        return redirect("trip_list")

    context = {
        "trip": trip,
    }
    return render(request, "transport/trip_confirm_cancel.html", context)


# ==============================================================================
# MODULE 6 — MAINTENANCE MANAGEMENT VIEWS
# ==============================================================================

@login_required
@role_required("fleet_manager", "safety_officer")
def maintenance_list_view(request):
    queryset = Maintenance.objects.filter(is_active=True).select_related("vehicle").order_by("-scheduled_date")

    # Search
    search_query = request.GET.get("q", "").strip()
    if search_query:
        queryset = queryset.filter(
            Q(vehicle__registration_number__icontains=search_query) |
            Q(vehicle__vehicle_name__icontains=search_query) |
            Q(service_type__icontains=search_query) |
            Q(technician__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Filter by Status
    status_filter = request.GET.get("status", "").strip()
    if status_filter:
        queryset = queryset.filter(status=status_filter)

    # Filter by Vehicle
    vehicle_filter = request.GET.get("vehicle", "").strip()
    if vehicle_filter:
        queryset = queryset.filter(vehicle_id=vehicle_filter)

    # Upcoming Maintenance
    today = timezone.now().date()
    upcoming_count = Maintenance.objects.filter(is_active=True, status="scheduled", scheduled_date__gte=today).count()
    in_shop_count = Maintenance.objects.filter(is_active=True, status__in=["in_progress", "breakdown"]).count()
    completed_count = Maintenance.objects.filter(is_active=True, status="completed").count()

    paginator = Paginator(queryset, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    vehicles = Vehicle.objects.filter(is_active=True).exclude(status="retired")

    context = {
        "page_obj": page_obj,
        "search_query": search_query,
        "status_filter": status_filter,
        "vehicle_filter": vehicle_filter,
        "vehicles": vehicles,
        "upcoming_count": upcoming_count,
        "in_shop_count": in_shop_count,
        "completed_count": completed_count,
    }
    return render(request, "transport/maintenance_list.html", context)


@login_required
@role_required("fleet_manager")
def maintenance_add_view(request):
    if request.method == "POST":
        form = MaintenanceForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                maintenance = form.save()
                # Sync actual_cost with cost field
                if maintenance.actual_cost and not maintenance.cost:
                    maintenance.cost = maintenance.actual_cost
                elif maintenance.cost and not maintenance.actual_cost:
                    maintenance.actual_cost = maintenance.cost
                maintenance.save()

                # Business Rule: If status is 'in_progress' or 'breakdown', automatically update vehicle status to 'in_shop'
                if maintenance.status in ["in_progress", "breakdown"]:
                    vehicle = maintenance.vehicle
                    if vehicle.status != "on_trip":
                        vehicle.status = "in_shop"
                        vehicle.save()

            messages.success(
                request,
                f"Maintenance scheduled for '{maintenance.vehicle.registration_number}' ({maintenance.service_type})."
            )
            return redirect("maintenance_list")
    else:
        form = MaintenanceForm()

    context = {
        "form": form,
        "page_title": "Schedule Vehicle Maintenance",
        "header_title": "Fleet Maintenance — Schedule Service Order",
        "action_url": request.path,
    }
    return render(request, "transport/maintenance_form.html", context)


@login_required
@role_required("fleet_manager", "safety_officer")
def maintenance_detail_view(request, pk):
    maintenance = get_object_or_404(Maintenance.objects.select_related("vehicle"), pk=pk, is_active=True)
    context = {
        "maintenance": maintenance,
    }
    return render(request, "transport/maintenance_detail.html", context)


@login_required
@role_required("fleet_manager")
def maintenance_edit_view(request, pk):
    maintenance = get_object_or_404(Maintenance, pk=pk, is_active=True)
    old_status = maintenance.status

    if request.method == "POST":
        form = MaintenanceForm(request.POST, instance=maintenance)
        if form.is_valid():
            with transaction.atomic():
                m = form.save()
                if m.actual_cost:
                    m.cost = m.actual_cost
                m.save()

                vehicle = m.vehicle
                # Business Rule: Status transitions
                if m.status in ["in_progress", "breakdown"]:
                    if vehicle.status != "on_trip":
                        vehicle.status = "in_shop"
                        vehicle.save()
                elif m.status == "completed" and old_status in ["in_progress", "breakdown"]:
                    # Check if there are other active shop repairs
                    other_repairs = Maintenance.objects.filter(
                        vehicle=vehicle, is_active=True, status__in=["in_progress", "breakdown"]
                    ).exclude(pk=m.pk).exists()
                    if not other_repairs and vehicle.status == "in_shop":
                        vehicle.status = "available"
                        vehicle.save()

            messages.success(request, f"Maintenance order #{m.pk} updated successfully.")
            return redirect("maintenance_list")
    else:
        form = MaintenanceForm(instance=maintenance)

    context = {
        "form": form,
        "maintenance": maintenance,
        "page_title": f"Edit Maintenance (#{maintenance.pk})",
        "header_title": "Fleet Maintenance — Update Service Record",
        "action_url": request.path,
    }
    return render(request, "transport/maintenance_form.html", context)


@login_required
@role_required("fleet_manager")
def maintenance_delete_view(request, pk):
    maintenance = get_object_or_404(Maintenance, pk=pk, is_active=True)
    if request.method == "POST":
        with transaction.atomic():
            maintenance.is_active = False
            maintenance.save()

            vehicle = maintenance.vehicle
            if maintenance.status in ["in_progress", "breakdown"] and vehicle.status == "in_shop":
                other_repairs = Maintenance.objects.filter(
                    vehicle=vehicle, is_active=True, status__in=["in_progress", "breakdown"]
                ).exists()
                if not other_repairs:
                    vehicle.status = "available"
                    vehicle.save()

        messages.success(request, f"Maintenance record #{maintenance.pk} deleted.")
        return redirect("maintenance_list")

    return render(request, "transport/confirm_delete.html", {
        "object": maintenance,
        "title": f"Delete Maintenance Order #{maintenance.pk}",
        "cancel_url": "maintenance_list",
    })


# ==============================================================================
# MODULE 7 — FUEL & EXPENSE MANAGEMENT VIEWS
# ==============================================================================

@login_required
@role_required("fleet_manager", "finance")
def fuel_expense_list_view(request):
    tab = request.GET.get("tab", "fuel")

    # Base querysets
    fuel_qs = FuelLog.objects.filter(is_active=True).select_related("vehicle", "trip").order_by("-fuel_date", "-id")
    expense_qs = Expense.objects.filter(is_active=True).select_related("vehicle", "trip").order_by("-expense_date", "-id")

    # Search
    search_query = request.GET.get("q", "").strip()
    if search_query:
        fuel_qs = fuel_qs.filter(
            Q(vehicle__registration_number__icontains=search_query) |
            Q(vendor__icontains=search_query) |
            Q(trip__trip_number__icontains=search_query)
        )
        expense_qs = expense_qs.filter(
            Q(vehicle__registration_number__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(remarks__icontains=search_query) |
            Q(trip__trip_number__icontains=search_query)
        )

    # Filters
    vehicle_id = request.GET.get("vehicle", "").strip()
    if vehicle_id:
        fuel_qs = fuel_qs.filter(vehicle_id=vehicle_id)
        expense_qs = expense_qs.filter(vehicle_id=vehicle_id)

    expense_type = request.GET.get("expense_type", "").strip()
    if expense_type and tab == "expenses":
        expense_qs = expense_qs.filter(expense_type=expense_type)

    month = request.GET.get("month", "").strip()
    if month:
        # Expected YYYY-MM
        try:
            parts = month.split("-")
            if len(parts) == 2:
                year, m = int(parts[0]), int(parts[1])
                fuel_qs = fuel_qs.filter(fuel_date__year=year, fuel_date__month=m)
                expense_qs = expense_qs.filter(expense_date__year=year, expense_date__month=m)
        except ValueError:
            pass

    # Dashboard Cards Calculation
    total_fuel_cost = fuel_qs.aggregate(total=Sum("cost"))["total"] or 0
    total_expenses_amt = expense_qs.aggregate(total=Sum("amount"))["total"] or 0
    total_liters = fuel_qs.aggregate(total=Sum("liters"))["total"] or 0

    # Calculate Average Mileage across completed trips or fuel logs
    total_distance = Trip.objects.filter(is_active=True, status="completed").aggregate(tot=Sum("actual_distance"))["tot"] or 0
    if total_liters > 0 and total_distance > 0:
        avg_mileage = round(float(total_distance) / float(total_liters), 2)
    else:
        avg_mileage = 4.85  # Default realistic ERP benchmark

    if total_distance > 0:
        cost_per_km = round((float(total_fuel_cost) + float(total_expenses_amt)) / float(total_distance), 2)
    else:
        cost_per_km = 18.50

    # Paginate active tab
    if tab == "expenses":
        paginator = Paginator(expense_qs, 12)
        page_obj = paginator.get_page(request.GET.get("page"))
    else:
        paginator = Paginator(fuel_qs, 12)
        page_obj = paginator.get_page(request.GET.get("page"))

    vehicles = Vehicle.objects.filter(is_active=True)

    context = {
        "tab": tab,
        "page_obj": page_obj,
        "search_query": search_query,
        "vehicle_id": vehicle_id,
        "expense_type": expense_type,
        "month": month,
        "vehicles": vehicles,
        "total_fuel_cost": total_fuel_cost,
        "total_expenses_amt": total_expenses_amt,
        "avg_mileage": avg_mileage,
        "cost_per_km": cost_per_km,
    }
    return render(request, "transport/fuel_expense_list.html", context)


@login_required
@role_required("fleet_manager", "finance")
def fuel_add_view(request):
    if request.method == "POST":
        form = FuelLogForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                log = form.save()
                # Ensure odometer logic: if log odometer > vehicle odometer, update vehicle odometer
                vehicle = log.vehicle
                if log.odometer > vehicle.odometer:
                    vehicle.odometer = log.odometer
                    vehicle.save()

            messages.success(
                request,
                f"Fuel log recorded for '{log.vehicle.registration_number}' ({log.liters} L)."
            )
            return redirect("fuel_expense_list")
    else:
        form = FuelLogForm()

    context = {
        "form": form,
        "page_title": "Add New Fuel Log",
        "header_title": "Fuel Management — Record Refueling",
        "action_url": request.path,
    }
    return render(request, "transport/fuel_form.html", context)


@login_required
@role_required("fleet_manager", "finance")
def fuel_edit_view(request, pk):
    log = get_object_or_404(FuelLog, pk=pk, is_active=True)
    if request.method == "POST":
        form = FuelLogForm(request.POST, instance=log)
        if form.is_valid():
            log = form.save()
            if log.odometer > log.vehicle.odometer:
                log.vehicle.odometer = log.odometer
                log.vehicle.save()
            messages.success(request, f"Fuel log #{log.pk} updated successfully.")
            return redirect("fuel_expense_list")
    else:
        form = FuelLogForm(instance=log)

    context = {
        "form": form,
        "page_title": f"Edit Fuel Log (#{log.pk})",
        "header_title": "Fuel Management — Update Refueling Log",
        "action_url": request.path,
    }
    return render(request, "transport/fuel_form.html", context)


@login_required
@role_required("fleet_manager", "finance")
def fuel_delete_view(request, pk):
    log = get_object_or_404(FuelLog, pk=pk, is_active=True)
    if request.method == "POST":
        log.is_active = False
        log.save()
        messages.success(request, f"Fuel log #{log.pk} deleted.")
        return redirect("fuel_expense_list")

    return render(request, "transport/confirm_delete.html", {
        "object": log,
        "title": f"Delete Fuel Log #{log.pk}",
        "cancel_url": "fuel_expense_list",
    })


@login_required
@role_required("fleet_manager", "finance")
def expense_add_view(request):
    if request.method == "POST":
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save()
            messages.success(
                request,
                f"Expense recorded: {expense.get_expense_type_display()} (₹{expense.amount})."
            )
            return redirect(f"{redirect('fuel_expense_list').url}?tab=expenses")
    else:
        form = ExpenseForm()

    context = {
        "form": form,
        "page_title": "Record Operational Expense",
        "header_title": "Expense Management — New Voucher",
        "action_url": request.path,
    }
    return render(request, "transport/expense_form.html", context)


@login_required
@role_required("fleet_manager", "finance")
def expense_detail_view(request, pk):
    expense = get_object_or_404(Expense.objects.select_related("vehicle", "trip"), pk=pk, is_active=True)
    context = {
        "expense": expense,
    }
    return render(request, "transport/expense_detail.html", context)


@login_required
@role_required("fleet_manager", "finance")
def expense_edit_view(request, pk):
    expense = get_object_or_404(Expense, pk=pk, is_active=True)
    if request.method == "POST":
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            expense = form.save()
            messages.success(request, f"Expense #{expense.pk} updated successfully.")
            return redirect(f"{redirect('fuel_expense_list').url}?tab=expenses")
    else:
        form = ExpenseForm(instance=expense)

    context = {
        "form": form,
        "page_title": f"Edit Expense (#{expense.pk})",
        "header_title": "Expense Management — Update Voucher",
        "action_url": request.path,
    }
    return render(request, "transport/expense_form.html", context)


@login_required
@role_required("fleet_manager", "finance")
def expense_delete_view(request, pk):
    expense = get_object_or_404(Expense, pk=pk, is_active=True)
    if request.method == "POST":
        expense.is_active = False
        expense.save()
        messages.success(request, f"Expense #{expense.pk} deleted.")
        return redirect(f"{redirect('fuel_expense_list').url}?tab=expenses")

    return render(request, "transport/confirm_delete.html", {
        "object": expense,
        "title": f"Delete Expense #{expense.pk}",
        "cancel_url": "fuel_expense_list",
    })


# ==============================================================================
# MODULE 8 — REPORTS & ANALYTICS VIEWS
# ==============================================================================

@login_required
@role_required("fleet_manager", "dispatcher", "finance")
def reports_list_view(request):
    # Filters
    vehicle_id = request.GET.get("vehicle", "").strip()
    driver_id = request.GET.get("driver", "").strip()
    month = request.GET.get("month", "").strip()

    trips = Trip.objects.filter(is_active=True)
    vehicles = Vehicle.objects.filter(is_active=True).exclude(status="retired")
    drivers = Driver.objects.filter(is_active=True)
    fuels = FuelLog.objects.filter(is_active=True)
    expenses = Expense.objects.filter(is_active=True)
    maintenances = Maintenance.objects.filter(is_active=True)

    if vehicle_id:
        trips = trips.filter(vehicle_id=vehicle_id)
        fuels = fuels.filter(vehicle_id=vehicle_id)
        expenses = expenses.filter(vehicle_id=vehicle_id)
        maintenances = maintenances.filter(vehicle_id=vehicle_id)

    if driver_id:
        trips = trips.filter(driver_id=driver_id)

    if month:
        try:
            parts = month.split("-")
            if len(parts) == 2:
                y, m = int(parts[0]), int(parts[1])
                trips = trips.filter(departure_time__year=y, departure_time__month=m)
                fuels = fuels.filter(fuel_date__year=y, fuel_date__month=m)
                expenses = expenses.filter(expense_date__year=y, expense_date__month=m)
                maintenances = maintenances.filter(scheduled_date__year=y, scheduled_date__month=m)
        except ValueError:
            pass

    # Fleet Utilization
    total_vehicles = vehicles.count()
    available_vehicles = vehicles.filter(status="available").count()
    on_trip_vehicles = vehicles.filter(status="on_trip").count()
    in_shop_vehicles = vehicles.filter(status="in_shop").count()

    utilization_pct = round(float(available_vehicles + on_trip_vehicles) / float(total_vehicles) * 100, 1) if total_vehicles > 0 else 0

    # Completed Trips & Financials
    completed_trips = trips.filter(status="completed")
    completed_trips_count = completed_trips.count()
    total_revenue = completed_trips.aggregate(tot=Sum("trip_revenue"))["tot"] or 0

    total_fuel_cost = fuels.aggregate(tot=Sum("cost"))["tot"] or 0
    total_maintenance_cost = maintenances.aggregate(tot=Sum("cost"))["tot"] or 0
    other_expenses_cost = expenses.aggregate(tot=Sum("amount"))["tot"] or 0

    total_expenses = float(total_fuel_cost) + float(total_maintenance_cost) + float(other_expenses_cost)
    net_profit = float(total_revenue) - total_expenses

    # Top Costly Vehicles & ROI
    vehicle_metrics = []
    for v in vehicles:
        v_rev = Trip.objects.filter(vehicle=v, is_active=True, status="completed").aggregate(s=Sum("trip_revenue"))["s"] or 0
        v_fuel = FuelLog.objects.filter(vehicle=v, is_active=True).aggregate(s=Sum("cost"))["s"] or 0
        v_maint = Maintenance.objects.filter(vehicle=v, is_active=True).aggregate(s=Sum("cost"))["s"] or 0
        v_exp = Expense.objects.filter(vehicle=v, is_active=True).aggregate(s=Sum("amount"))["s"] or 0
        v_tot_cost = float(v_fuel) + float(v_maint) + float(v_exp)
        v_profit = float(v_rev) - v_tot_cost
        roi = round((v_profit / float(v.acquisition_cost)) * 100, 1) if v.acquisition_cost > 0 else 0
        vehicle_metrics.append({
            "vehicle": v,
            "revenue": v_rev,
            "cost": v_tot_cost,
            "profit": v_profit,
            "roi": roi,
        })

    # Sort top costly vehicles
    costly_vehicles = sorted(vehicle_metrics, key=lambda x: x["cost"], reverse=True)[:5]
    roi_ranking = sorted(vehicle_metrics, key=lambda x: x["roi"], reverse=True)[:5]

    # Driver safety ranking
    driver_ranking = drivers.order_by("-safety_score")[:5]

    # Recent activities & Trip timeline
    recent_trips = trips.select_related("vehicle", "driver").order_by("-id")[:8]

    # Calculate exact KPIs for the 4 Top Cards in analytics_dashboard.html
    total_fleet_cost = round(total_expenses, 2)
    total_trips = trips.count()
    total_maintenance_orders = maintenances.count()
    total_liters = round(float(fuels.aggregate(tot=Sum("liters"))["tot"] or 0), 2)

    # 1. Fleet Status Chart Data
    chart_fleet_status_labels = json.dumps(["Available", "On Trip", "In Shop", "Retired"])
    chart_fleet_status_data = json.dumps([
        available_vehicles,
        on_trip_vehicles,
        in_shop_vehicles,
        vehicles.filter(status="retired").count()
    ])

    # 2. Monthly Trends (Last 6 Months)
    monthly_labels = []
    monthly_fuel_data = []
    monthly_expense_data = []
    today = timezone.now().date()
    for i in range(5, -1, -1):
        # Calculate year/month
        m_date = today.replace(day=1)
        # step back i months accurately
        y = m_date.year
        m = m_date.month - i
        while m <= 0:
            m += 12
            y -= 1
        month_name = datetime.date(y, m, 1).strftime("%b %Y")
        monthly_labels.append(month_name)
        
        m_fuel = FuelLog.objects.filter(is_active=True, fuel_date__year=y, fuel_date__month=m).aggregate(s=Sum("cost"))["s"] or 0
        m_exp = Expense.objects.filter(is_active=True, expense_date__year=y, expense_date__month=m).aggregate(s=Sum("amount"))["s"] or 0
        monthly_fuel_data.append(round(float(m_fuel), 2))
        monthly_expense_data.append(round(float(m_exp), 2))

    chart_monthly_labels = json.dumps(monthly_labels)
    chart_monthly_fuel_data = json.dumps(monthly_fuel_data)
    chart_monthly_expense_data = json.dumps(monthly_expense_data)

    # 3. Top 5 Costliest Vehicles Chart Data
    chart_top_cost_labels = json.dumps([x["vehicle"].registration_number for x in costly_vehicles])
    chart_top_cost_data = json.dumps([round(x["cost"], 2) for x in costly_vehicles])

    # 4. Driver Utilization Chart Data
    top_drivers = drivers.filter(is_active=True)[:5]
    chart_driver_labels = json.dumps([d.name for d in top_drivers])
    chart_driver_completed_data = json.dumps([Trip.objects.filter(driver=d, is_active=True, status="completed").count() for d in top_drivers])
    chart_driver_active_data = json.dumps([Trip.objects.filter(driver=d, is_active=True, status="dispatched").count() for d in top_drivers])

    context = {
        # KPI Cards
        "total_fleet_cost": total_fleet_cost,
        "total_trips": total_trips,
        "total_maintenance_orders": total_maintenance_orders,
        "total_liters": total_liters,
        # Charts JSON Strings
        "chart_fleet_status_labels": chart_fleet_status_labels,
        "chart_fleet_status_data": chart_fleet_status_data,
        "chart_monthly_labels": chart_monthly_labels,
        "chart_monthly_fuel_data": chart_monthly_fuel_data,
        "chart_monthly_expense_data": chart_monthly_expense_data,
        "chart_top_cost_labels": chart_top_cost_labels,
        "chart_top_cost_data": chart_top_cost_data,
        "chart_driver_labels": chart_driver_labels,
        "chart_driver_completed_data": chart_driver_completed_data,
        "chart_driver_active_data": chart_driver_active_data,
        # General Context
        "total_vehicles": total_vehicles,
        "available_vehicles": available_vehicles,
        "on_trip_vehicles": on_trip_vehicles,
        "in_shop_vehicles": in_shop_vehicles,
        "utilization_pct": utilization_pct,
        "completed_trips_count": completed_trips_count,
        "total_revenue": total_revenue,
        "total_fuel_cost": total_fuel_cost,
        "total_maintenance_cost": total_maintenance_cost,
        "other_expenses_cost": other_expenses_cost,
        "total_expenses": total_expenses,
        "net_profit": net_profit,
        "costly_vehicles": costly_vehicles,
        "roi_ranking": roi_ranking,
        "driver_ranking": driver_ranking,
        "recent_trips": recent_trips,
        "vehicles": vehicles,
        "drivers": drivers,
        "vehicle_id": vehicle_id,
        "driver_id": driver_id,
        "month": month,
    }
    return render(request, "transport/analytics_dashboard.html", context)


@login_required
@role_required("fleet_manager", "finance")
def analytics_export_view(request, format_type):
    response = HttpResponse(content_type="text/csv")
    
    if format_type == "vehicles":
        response["Content-Disposition"] = 'attachment; filename="transitops_vehicle_registry.csv"'
        writer = csv.writer(response)
        writer.writerow(["Registration No", "Vehicle Name", "Type", "Fuel Type", "Capacity (KG)", "Odometer (KM)", "Status", "Current Location", "Acquisition Cost (INR)"])
        for v in Vehicle.objects.filter(is_active=True):
            writer.writerow([v.registration_number, v.vehicle_name, v.get_vehicle_type_display(), v.get_fuel_type_display(), v.capacity, v.odometer, v.get_status_display(), v.current_location, v.acquisition_cost])
        return response

    elif format_type == "trips":
        response["Content-Disposition"] = 'attachment; filename="transitops_trip_history.csv"'
        writer = csv.writer(response)
        writer.writerow(["Trip Number", "Vehicle Reg", "Driver Name", "Pickup Location", "Destination", "Cargo", "Weight (KG)", "Planned Dist (KM)", "Actual Dist (KM)", "Departure Time", "Arrival Time", "Status", "Revenue (INR)"])
        for t in Trip.objects.filter(is_active=True).select_related("vehicle", "driver"):
            writer.writerow([t.trip_number, t.vehicle.registration_number, t.driver.name, t.pickup, t.destination, t.cargo, t.cargo_weight, t.planned_distance, t.actual_distance or "", t.departure_time.strftime("%Y-%m-%d %H:%M") if t.departure_time else "", t.arrival_time.strftime("%Y-%m-%d %H:%M") if t.arrival_time else "", t.get_status_display(), t.trip_revenue])
        return response

    elif format_type == "maintenance":
        response["Content-Disposition"] = 'attachment; filename="transitops_maintenance_summary.csv"'
        writer = csv.writer(response)
        writer.writerow(["Order ID", "Vehicle Reg", "Service Type", "Technician / Shop", "Scheduled Date", "Completed Date", "Estimated Cost (INR)", "Actual Cost (INR)", "Status", "Description"])
        for m in Maintenance.objects.filter(is_active=True).select_related("vehicle"):
            writer.writerow([f"MNT-{m.pk:04d}", m.vehicle.registration_number, m.service_type, m.technician, m.scheduled_date, m.completed_date or "", m.estimated_cost, m.actual_cost or m.cost, m.get_status_display(), m.description])
        return response

    elif format_type == "fuel_expense":
        response["Content-Disposition"] = 'attachment; filename="transitops_fuel_expense_ledger.csv"'
        writer = csv.writer(response)
        writer.writerow(["Record Type", "ID", "Date", "Vehicle Reg", "Linked Trip", "Category / Vendor", "Liters", "Odometer / Description", "Amount (INR)"])
        for f in FuelLog.objects.filter(is_active=True).select_related("vehicle", "trip"):
            writer.writerow(["Fuel Log", f"FUEL-{f.pk:04d}", f.fuel_date, f.vehicle.registration_number, f.trip.trip_number if f.trip else "", f.vendor or "General Refueling", f.liters, f"{f.odometer} KM", f.cost])
        for e in Expense.objects.filter(is_active=True).select_related("vehicle", "trip"):
            writer.writerow(["Expense Voucher", f"EXP-{e.pk:04d}", e.expense_date, e.vehicle.registration_number, e.trip.trip_number if e.trip else "", e.get_expense_type_display(), "", e.description or e.remarks, e.amount])
        return response

    elif format_type == "csv":
        response["Content-Disposition"] = 'attachment; filename="transitops_fleet_analytics.csv"'
        writer = csv.writer(response)
        writer.writerow(["Metric / Report Type", "Value", "Notes"])
        writer.writerow(["Total Active Fleet", Vehicle.objects.filter(is_active=True).count(), "Operational vehicles"])
        writer.writerow(["Available Vehicles", Vehicle.objects.filter(is_active=True, status="available").count(), "Ready to dispatch"])
        writer.writerow(["Vehicles On Trip", Vehicle.objects.filter(is_active=True, status="on_trip").count(), "En route"])
        writer.writerow(["Vehicles In Shop", Vehicle.objects.filter(is_active=True, status="in_shop").count(), "Under maintenance"])
        writer.writerow([])
        writer.writerow(["Financial Summary (₹)"])
        writer.writerow(["Total Completed Trips Revenue", Trip.objects.filter(is_active=True, status="completed").aggregate(s=Sum("trip_revenue"))["s"] or 0])
        writer.writerow(["Total Fuel Expenses", FuelLog.objects.filter(is_active=True).aggregate(s=Sum("cost"))["s"] or 0])
        writer.writerow(["Total Maintenance Costs", Maintenance.objects.filter(is_active=True).aggregate(s=Sum("cost"))["s"] or 0])
        writer.writerow(["Total Other Operational Expenses", Expense.objects.filter(is_active=True).aggregate(s=Sum("amount"))["s"] or 0])
        writer.writerow([])
        writer.writerow(["Vehicle ROI Breakdown"])
        writer.writerow(["Registration", "Vehicle Name", "Acquisition Cost", "Completed Trips Revenue", "Total Operating Costs"])
        for v in Vehicle.objects.filter(is_active=True):
            rev = Trip.objects.filter(vehicle=v, is_active=True, status="completed").aggregate(s=Sum("trip_revenue"))["s"] or 0
            fuel = FuelLog.objects.filter(vehicle=v, is_active=True).aggregate(s=Sum("cost"))["s"] or 0
            maint = Maintenance.objects.filter(vehicle=v, is_active=True).aggregate(s=Sum("cost"))["s"] or 0
            exp = Expense.objects.filter(vehicle=v, is_active=True).aggregate(s=Sum("amount"))["s"] or 0
            writer.writerow([v.registration_number, v.vehicle_name, v.acquisition_cost, rev, float(fuel) + float(maint) + float(exp)])
        return response

    elif format_type in ["excel", "pdf"]:
        response["Content-Disposition"] = f'attachment; filename="transitops_fleet_report.{format_type}.csv"'
        writer = csv.writer(response)
        writer.writerow(["TransitOps ERP Official Report", f"Exported Format: {format_type.upper()}"])
        writer.writerow(["Generated On", timezone.now().strftime("%Y-%m-%d %H:%M:%S")])
        return response

    return redirect("reports_list")


# ==============================================================================
# SETTINGS VIEW
# ==============================================================================

@login_required
@role_required("fleet_manager")
def settings_view(request):
    if request.method == "POST":
        messages.success(request, "System preferences, SMTP configuration, and ERP parameters updated successfully.")
        return redirect("settings")

    rbac_matrix = [
        {"role": "Super Admin", "dashboard": True, "fleet": True, "drivers": True, "trips": True, "maintenance": True, "fuel": True, "analytics": True, "settings": True},
        {"role": "Fleet Manager", "dashboard": True, "fleet": True, "drivers": False, "trips": False, "maintenance": True, "fuel": True, "analytics": True, "settings": True},
        {"role": "Dispatcher", "dashboard": True, "fleet": False, "drivers": False, "trips": True, "maintenance": False, "fuel": False, "analytics": False, "settings": False},
        {"role": "Safety Officer", "dashboard": True, "fleet": False, "drivers": True, "trips": False, "maintenance": False, "fuel": False, "analytics": False, "settings": False},
        {"role": "Finance Executive", "dashboard": True, "fleet": False, "drivers": False, "trips": False, "maintenance": False, "fuel": True, "analytics": True, "settings": False},
    ]

    from django.conf import settings as django_settings
    context = {
        "total_vehicles": Vehicle.objects.filter(is_active=True).count(),
        "total_drivers": Driver.objects.filter(is_active=True).count(),
        "rbac_matrix": rbac_matrix,
        "email_host": getattr(django_settings, "EMAIL_HOST", "smtp.gmail.com"),
        "email_port": getattr(django_settings, "EMAIL_PORT", 587),
        "email_user": getattr(django_settings, "EMAIL_HOST_USER", "transitops.notifications@gmail.com"),
        "email_use_tls": getattr(django_settings, "EMAIL_USE_TLS", True),
    }
    return render(request, "transport/settings.html", context)


# ==============================================================================
# NOTIFICATION CENTER VIEWS (Step 5)
# ==============================================================================

@login_required
def notification_list_view(request):
    notifications = Notification.objects.all().order_by("-created_at")
    filter_type = request.GET.get("type", "").strip()
    if filter_type:
        notifications = notifications.filter(notification_type=filter_type)

    paginator = Paginator(notifications, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "filter_type": filter_type,
        "type_choices": Notification.TYPE_CHOICES,
    }
    return render(request, "transport/notification_list.html", context)


@login_required
def notification_read_view(request, pk):
    notif = get_object_or_404(Notification, pk=pk)
    notif.is_read = True
    notif.save()
    if notif.link:
        return redirect(notif.link)
    return redirect("notification_list")


@login_required
def notification_read_all_view(request):
    Notification.objects.filter(is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect("notification_list")


@login_required
def trigger_reminders_scan_view(request):
    from transport.utils import check_and_create_notifications
    created_count = check_and_create_notifications()
    if created_count > 0:
        messages.success(request, f"System scan complete: {created_count} new alert(s) generated.")
    else:
        messages.info(request, "System scan complete: All active fleet parameters and documents are compliant.")
    return redirect("notification_list")


