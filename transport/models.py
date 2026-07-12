from django.db import models


class Vehicle(models.Model):
    STATUS_CHOICES = [
        ("available", "Available"),
        ("on_trip", "On Trip"),
        ("in_shop", "In Shop"),
        ("retired", "Retired"),
    ]

    FUEL_CHOICES = [
        ("diesel", "Diesel"),
        ("petrol", "Petrol"),
        ("cng", "CNG"),
        ("electric", "Electric"),
    ]

    VEHICLE_TYPES = [
        ("truck", "Truck"),
        ("van", "Van"),
        ("pickup", "Pickup"),
        ("bus", "Bus"),
    ]

    registration_number = models.CharField(max_length=20, unique=True)
    vehicle_name = models.CharField(max_length=100)
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES)
    fuel_type = models.CharField(max_length=20, choices=FUEL_CHOICES)

    capacity = models.PositiveIntegerField(help_text="Capacity in KG")
    odometer = models.PositiveIntegerField(default=0)

    acquisition_cost = models.DecimalField(max_digits=12, decimal_places=2)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="available"
    )

    insurance_expiry = models.DateField()

    current_location = models.CharField(
        max_length=100,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.registration_number} - {self.vehicle_name}"
    
class Driver(models.Model):
    STATUS_CHOICES = [
        ("available", "Available"),
        ("on_trip", "On Trip"),
        ("off_duty", "Off Duty"),
        ("suspended", "Suspended"),
    ]

    name = models.CharField(max_length=100)
    license_number = models.CharField(max_length=50, unique=True)
    license_category = models.CharField(max_length=20)
    license_expiry = models.DateField()

    phone = models.CharField(max_length=15)
    emergency_contact = models.CharField(max_length=15, blank=True)

    safety_score = models.PositiveIntegerField(default=100)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="available"
    )

    joining_date = models.DateField(
        auto_now_add=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Trip(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("dispatched", "Dispatched"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    trip_number = models.CharField(max_length=20, unique=True)

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.PROTECT,
        related_name="trips"
    )

    driver = models.ForeignKey(
        Driver,
        on_delete=models.PROTECT,
        related_name="trips"
    )

    pickup = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)

    cargo = models.CharField(max_length=100)
    cargo_weight = models.PositiveIntegerField(help_text="Weight in KG")

    planned_distance = models.PositiveIntegerField(help_text="Distance in KM")
    actual_distance = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    start_odometer = models.PositiveIntegerField()

    end_odometer = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    fuel_consumed = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Liters"
    )

    trip_revenue = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft"
    )

    remarks = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.trip_number
    
class Maintenance(models.Model):
    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("breakdown", "Breakdown"),
    ]

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name="maintenances"
    )

    service_type = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    technician = models.CharField(max_length=100)

    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    scheduled_date = models.DateField()

    completed_date = models.DateField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="scheduled"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.vehicle} - {self.service_type}"
    
class FuelLog(models.Model):
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name="fuel_logs"
    )

    trip = models.ForeignKey(
        Trip,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fuel_logs"
    )

    fuel_date = models.DateField()

    liters = models.DecimalField(
        max_digits=8,
        decimal_places=2
    )

    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    odometer = models.PositiveIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.vehicle} - {self.fuel_date}"
    
class Expense(models.Model):
    EXPENSE_CHOICES = [
        ("fuel", "Fuel"),
        ("maintenance", "Maintenance"),
        ("toll", "Toll"),
        ("parking", "Parking"),
        ("other", "Other"),
    ]

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name="expenses"
    )

    trip = models.ForeignKey(
        Trip,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="expenses"
    )

    expense_type = models.CharField(
        max_length=20,
        choices=EXPENSE_CHOICES
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expense_date = models.DateField()

    def __str__(self):
        return f"{self.expense_type} - ₹{self.amount}"