from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.shortcuts import render
from django.utils import timezone
from transport.models import Vehicle, Driver, Trip, Maintenance, FuelLog, Expense


@login_required
def dashboard_view(request):
    vehicle_type = request.GET.get("vehicle_type", "").strip()
    status_filter = request.GET.get("status", "").strip()
    region_filter = request.GET.get("region", "").strip()

    vehicles_qs = Vehicle.objects.filter(is_active=True)
    if vehicle_type:
        vehicles_qs = vehicles_qs.filter(vehicle_type=vehicle_type)
    if status_filter:
        vehicles_qs = vehicles_qs.filter(status=status_filter)
    if region_filter:
        vehicles_qs = vehicles_qs.filter(current_location__icontains=region_filter)

    total_vehicles = vehicles_qs.count()
    active_vehicles = vehicles_qs.exclude(status="retired").count()
    available_vehicles = vehicles_qs.filter(status="available").count()
    in_shop_vehicles = vehicles_qs.filter(status="in_shop").count()
    on_trip_vehicles = vehicles_qs.filter(status="on_trip").count()
    retired_vehicles = vehicles_qs.filter(status="retired").count()

    active_trips = Trip.objects.filter(is_active=True, status="dispatched").count()
    pending_trips = Trip.objects.filter(is_active=True, status="draft").count()
    drivers_on_duty = Driver.objects.filter(is_active=True, status="on_trip").count() + Driver.objects.filter(is_active=True, status="available").count()

    utilization_pct = f"{round((available_vehicles + on_trip_vehicles) / total_vehicles * 100, 1)}%" if total_vehicles > 0 else "0.0%"

    kpis = {
        "active_vehicles": active_vehicles,
        "available_vehicles": available_vehicles,
        "vehicles_in_maintenance": in_shop_vehicles,
        "active_trips": active_trips,
        "pending_trips": pending_trips,
        "drivers_on_duty": drivers_on_duty,
        "fleet_utilization": utilization_pct,
    }

    # Calculate status percentages
    tot = total_vehicles or 1
    vehicle_status_summary = {
        "available": {"count": available_vehicles, "percentage": round(available_vehicles / tot * 100)},
        "on_trip": {"count": on_trip_vehicles, "percentage": round(on_trip_vehicles / tot * 100)},
        "in_shop": {"count": in_shop_vehicles, "percentage": round(in_shop_vehicles / tot * 100)},
        "retired": {"count": retired_vehicles, "percentage": round(retired_vehicles / tot * 100)},
        "total": total_vehicles,
    }

    # Query recent trips
    recent_trips_qs = Trip.objects.filter(is_active=True).select_related("vehicle", "driver").order_by("-id")[:5]
    recent_trips = []
    for t in recent_trips_qs:
        status_class = "bg-slate-50 text-slate-700 border-slate-200"
        if t.status == "dispatched":
            status_class = "bg-blue-50 text-blue-700 border-blue-200"
        elif t.status == "completed":
            status_class = "bg-green-50 text-green-700 border-green-200"
        elif t.status == "draft":
            status_class = "bg-amber-50 text-amber-700 border-amber-200"
        elif t.status == "cancelled":
            status_class = "bg-red-50 text-red-700 border-red-200"

        recent_trips.append({
            "trip": t.trip_number,
            "vehicle": str(t.vehicle),
            "driver": str(t.driver),
            "status": t.get_status_display(),
            "eta": t.departure_time.strftime("%d %b %H:%M") if t.departure_time else "N/A",
            "status_class": status_class,
        })

    # Upcoming Maintenance for Dashboard display
    today = timezone.now().date()
    upcoming_maintenance = Maintenance.objects.filter(
        is_active=True, status="scheduled", scheduled_date__gte=today
    ).select_related("vehicle").order_by("scheduled_date")[:5]

    # Additional Quick Stats for Dashboard
    total_fuel_cost = FuelLog.objects.filter(is_active=True).aggregate(t=Sum("cost"))["t"] or 0
    total_expenses = Expense.objects.filter(is_active=True).aggregate(t=Sum("amount"))["t"] or 0

    context = {
        "kpis": kpis,
        "recent_trips": recent_trips,
        "vehicle_status_summary": vehicle_status_summary,
        "upcoming_maintenance": upcoming_maintenance,
        "total_fuel_cost": total_fuel_cost,
        "total_expenses": total_expenses,
    }
    return render(request, "dashboard/dashboard.html", context)
