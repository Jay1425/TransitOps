from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def dashboard_view(request):
    # Temporary realistic ERP values as requested for Module 2 layout
    kpis = {
        "active_vehicles": 142,
        "available_vehicles": 98,
        "vehicles_in_maintenance": 12,
        "active_trips": 32,
        "pending_trips": 18,
        "drivers_on_duty": 115,
        "fleet_utilization": "78.4%",
    }

    recent_trips = [
        {"trip": "TRP-2026-0891", "vehicle": "MH-12-PQ-4512 (Volvo FH16)", "driver": "Rajesh Kumar", "status": "On Trip", "eta": "2 hrs 15 mins", "status_class": "bg-blue-50 text-blue-700 border-blue-200"},
        {"trip": "TRP-2026-0890", "vehicle": "DL-01-AB-9012 (Tata Prima)", "driver": "Vikram Singh", "status": "Completed", "eta": "Arrived", "status_class": "bg-green-50 text-green-700 border-green-200"},
        {"trip": "TRP-2026-0889", "vehicle": "KA-04-XY-3321 (BharatBenz 5528)", "driver": "Suresh Sharma", "status": "Dispatched", "eta": "5 hrs 40 mins", "status_class": "bg-indigo-50 text-indigo-700 border-indigo-200"},
        {"trip": "TRP-2026-0888", "vehicle": "MH-04-EF-7711 (Ashok Leyland)", "driver": "Amit Patel", "status": "Delayed", "eta": "+1 hr delay", "status_class": "bg-amber-50 text-amber-700 border-amber-200"},
        {"trip": "TRP-2026-0887", "vehicle": "GJ-01-KL-8822 (Mahindra Blazo)", "driver": "Pramod Verma", "status": "In Shop", "eta": "N/A", "status_class": "bg-red-50 text-red-700 border-red-200"},
    ]

    vehicle_status_summary = {
        "available": {"count": 98, "percentage": 66},
        "on_trip": {"count": 32, "percentage": 22},
        "in_shop": {"count": 12, "percentage": 8},
        "retired": {"count": 6, "percentage": 4},
        "total": 148,
    }

    context = {
        "kpis": kpis,
        "recent_trips": recent_trips,
        "vehicle_status_summary": vehicle_status_summary,
    }
    return render(request, "dashboard/dashboard.html", context)