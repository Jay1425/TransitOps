from django.urls import path
from . import views

urlpatterns = [
    # Module 3 - Vehicle Registry
    path("fleet/", views.vehicle_list_view, name="vehicle_list"),
    path("fleet/add/", views.vehicle_add_view, name="vehicle_add"),
    path("fleet/<int:pk>/", views.vehicle_detail_view, name="vehicle_detail"),
    path("fleet/<int:pk>/edit/", views.vehicle_edit_view, name="vehicle_edit"),
    path("fleet/<int:pk>/delete/", views.vehicle_delete_view, name="vehicle_delete"),
    path("fleet/<int:pk>/document-upload/", views.document_upload_view, name="document_upload"),
    path("documents/<int:pk>/delete/", views.document_delete_view, name="document_delete"),

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

    # Module 6 - Maintenance Management
    path("maintenance/", views.maintenance_list_view, name="maintenance_list"),
    path("maintenance/add/", views.maintenance_add_view, name="maintenance_add"),
    path("maintenance/<int:pk>/", views.maintenance_detail_view, name="maintenance_detail"),
    path("maintenance/<int:pk>/edit/", views.maintenance_edit_view, name="maintenance_edit"),
    path("maintenance/<int:pk>/delete/", views.maintenance_delete_view, name="maintenance_delete"),

    # Module 7 - Fuel & Expense Management
    path("fuel/", views.fuel_expense_list_view, name="fuel_expense_list"),
    path("fuel/add/", views.fuel_add_view, name="fuel_add"),
    path("fuel/<int:pk>/edit/", views.fuel_edit_view, name="fuel_edit"),
    path("fuel/<int:pk>/delete/", views.fuel_delete_view, name="fuel_delete"),
    path("expenses/add/", views.expense_add_view, name="expense_add"),
    path("expenses/<int:pk>/", views.expense_detail_view, name="expense_detail"),
    path("expenses/<int:pk>/edit/", views.expense_edit_view, name="expense_edit"),
    path("expenses/<int:pk>/delete/", views.expense_delete_view, name="expense_delete"),

    # Module 8 - Reports & Analytics
    path("analytics/", views.reports_list_view, name="reports_list"),
    path("analytics/export/<str:format_type>/", views.analytics_export_view, name="analytics_export"),

    # Notification Center
    path("notifications/", views.notification_list_view, name="notification_list"),
    path("notifications/<int:pk>/read/", views.notification_read_view, name="notification_read"),
    path("notifications/read-all/", views.notification_read_all_view, name="notification_read_all"),
    path("notifications/scan/", views.trigger_reminders_scan_view, name="trigger_reminders_scan"),

    # Settings
    path("settings/", views.settings_view, name="settings"),
]

