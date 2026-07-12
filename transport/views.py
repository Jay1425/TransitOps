from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from accounts.decorators import role_required
from .forms import DriverForm, TripCompleteForm, TripForm, VehicleForm
from .models import Driver, Trip, Vehicle


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

    context = {
        "vehicle": vehicle,
        "recent_trips": recent_trips,
        "maintenance_logs": maintenance_logs,
        "fuel_logs": fuel_logs,
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

            if not vehicle or not vehicle.is_active or vehicle.status != "available":
                messages.error(request, f"Assigned vehicle '{vehicle.registration_number if vehicle else 'None'}' is no longer available for dispatch.")
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
# PLACEHOLDERS FOR MODULES 6, 7, 8 & SETTINGS
# ==============================================================================

@login_required
@role_required("fleet_manager")
def maintenance_list_view(request):
    return render(request, "transport/coming_soon.html", {
        "module_title": "Fleet Maintenance & Shop Logs",
        "module_path": "/maintenance/",
        "scheduled_module": "Module 6",
        "description": "Service scheduling, repair costs, technician tracking, and vehicle availability synchronization.",
        "allowed_roles": "Super Admin, Fleet Manager"
    })


@login_required
@role_required("fleet_manager", "finance")
def fuel_expense_list_view(request):
    return render(request, "transport/coming_soon.html", {
        "module_title": "Fuel Logs & Operational Expenses",
        "module_path": "/fuel/",
        "scheduled_module": "Module 7",
        "description": "Liter tracking, fuel cost calculations, trip-linked expenses, and financial audit logs.",
        "allowed_roles": "Super Admin, Fleet Manager, Finance Executive"
    })


@login_required
@role_required("fleet_manager", "finance")
def reports_list_view(request):
    return render(request, "transport/coming_soon.html", {
        "module_title": "Operational Analytics & ROI Reports",
        "module_path": "/analytics/",
        "scheduled_module": "Module 8",
        "description": "Fuel efficiency charts, cost per kilometer analysis, vehicle ROI computation, and CSV exports.",
        "allowed_roles": "Super Admin, Fleet Manager, Finance Executive"
    })


@login_required
@role_required("fleet_manager")
def settings_view(request):
    return render(request, "transport/coming_soon.html", {
        "module_title": "System Configuration & ERP Settings",
        "module_path": "/settings/",
        "scheduled_module": "Settings & Admin",
        "description": "Fleet configuration, default parameters, notification preferences, and system maintenance logs.",
        "allowed_roles": "Super Admin, Fleet Manager"
    })
