from django.urls import path
from . import views

urlpatterns = [
    # Module 3 - Vehicle Registry
    path("fleet/", views.vehicle_list_view, name="vehicle_list"),
    path("fleet/add/", views.vehicle_add_view, name="vehicle_add"),
    path("fleet/<int:pk>/", views.vehicle_detail_view, name="vehicle_detail"),
    path("fleet/<int:pk>/edit/", views.vehicle_edit_view, name="vehicle_edit"),
    path("fleet/<int:pk>/delete/", views.vehicle_delete_view, name="vehicle_delete"),

    # Module 4 - Driver Management
    path("drivers/", views.driver_list_view, name="driver_list"),
    path("drivers/add/", views.driver_add_view, name="driver_add"),
    path("drivers/<int:pk>/edit/", views.driver_edit_view, name="driver_edit"),
    path("drivers/<int:pk>/delete/", views.driver_delete_view, name="driver_delete"),

    # Module 5 - Trip Management
    path("trips/", views.trip_list_view, name="trip_list"),
    path("trips/add/", views.trip_add_view, name="trip_add"),
    path("trips/<int:pk>/edit/", views.trip_edit_view, name="trip_edit"),
    path("trips/<int:pk>/dispatch/", views.trip_dispatch_view, name="trip_dispatch"),
    path("trips/<int:pk>/complete/", views.trip_complete_view, name="trip_complete"),
    path("trips/<int:pk>/cancel/", views.trip_cancel_view, name="trip_cancel"),

    # Modules 6, 7, 8 & Settings placeholders
    path("maintenance/", views.maintenance_list_view, name="maintenance_list"),
    path("fuel/", views.fuel_expense_list_view, name="fuel_expense_list"),
    path("analytics/", views.reports_list_view, name="reports_list"),
    path("settings/", views.settings_view, name="settings"),
]
