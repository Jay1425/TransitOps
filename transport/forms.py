from django import forms
from django.utils import timezone
from .models import Vehicle, Driver, Trip, Maintenance, FuelLog, Expense


class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = [
            "registration_number",
            "vehicle_name",
            "vehicle_type",
            "fuel_type",
            "capacity",
            "odometer",
            "acquisition_cost",
            "status",
            "insurance_expiry",
            "current_location",
        ]
        widgets = {
            "registration_number": forms.TextInput(attrs={"class": "form-input w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30 uppercase font-mono placeholder-slate-400", "placeholder": "e.g. MH-12-PQ-4512"}),
            "vehicle_name": forms.TextInput(attrs={"class": "form-input w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30 placeholder-slate-400", "placeholder": "e.g. Volvo FH16 540"}),
            "vehicle_type": forms.Select(attrs={"class": "form-select w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30"}),
            "fuel_type": forms.Select(attrs={"class": "form-select w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30"}),
            "capacity": forms.NumberInput(attrs={"class": "form-input w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30 placeholder-slate-400", "placeholder": "Capacity in KG (e.g. 25000)", "min": "1"}),
            "odometer": forms.NumberInput(attrs={"class": "form-input w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30 placeholder-slate-400", "placeholder": "Current KM (e.g. 12540)", "min": "0"}),
            "acquisition_cost": forms.NumberInput(attrs={"class": "form-input w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30 placeholder-slate-400", "placeholder": "Cost in ₹", "step": "0.01", "min": "0"}),
            "status": forms.Select(attrs={"class": "form-select w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30"}),
            "insurance_expiry": forms.DateInput(format="%Y-%m-%d", attrs={"class": "form-input w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30", "type": "date"}),
            "current_location": forms.TextInput(attrs={"class": "form-input w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30 placeholder-slate-400", "placeholder": "e.g. Pune Depot / Terminal 3"}),
        }

    def clean_registration_number(self):
        reg = self.cleaned_data.get("registration_number", "").strip().upper()
        qs = Vehicle.objects.filter(registration_number=reg)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("A vehicle with this registration number already exists.")
        return reg

    def clean_capacity(self):
        cap = self.cleaned_data.get("capacity")
        if cap is not None and cap <= 0:
            raise forms.ValidationError("Capacity must be greater than zero.")
        return cap


class DriverForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = [
            "name",
            "license_number",
            "license_category",
            "license_expiry",
            "phone",
            "emergency_contact",
            "safety_score",
            "status",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30 placeholder-slate-400", "placeholder": "Driver Full Name"}),
            "license_number": forms.TextInput(attrs={"class": "form-input w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30 font-mono uppercase placeholder-slate-400", "placeholder": "e.g. DL-1420110012345"}),
            "license_category": forms.TextInput(attrs={"class": "form-input w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30 uppercase placeholder-slate-400", "placeholder": "e.g. HMV / HTV"}),
            "license_expiry": forms.DateInput(format="%Y-%m-%d", attrs={"class": "form-input w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30", "type": "date"}),
            "phone": forms.TextInput(attrs={"class": "form-input w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30 placeholder-slate-400", "placeholder": "e.g. +91 98765 43210"}),
            "emergency_contact": forms.TextInput(attrs={"class": "form-input w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30 placeholder-slate-400", "placeholder": "Emergency contact number"}),
            "safety_score": forms.NumberInput(attrs={"class": "form-input w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30 placeholder-slate-400", "min": "0", "max": "100"}),
            "status": forms.Select(attrs={"class": "form-select w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30"}),
        }

    def clean_license_number(self):
        lic = self.cleaned_data.get("license_number", "").strip().upper()
        qs = Driver.objects.filter(license_number=lic)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("A driver with this license number already exists.")
        return lic

    def clean_safety_score(self):
        score = self.cleaned_data.get("safety_score")
        if score is not None and (score < 0 or score > 100):
            raise forms.ValidationError("Safety score must be between 0 and 100.")
        return score


class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = [
            "trip_number",
            "pickup",
            "destination",
            "vehicle",
            "driver",
            "cargo",
            "cargo_weight",
            "planned_distance",
            "departure_time",
            "remarks",
        ]
        widgets = {
            "trip_number": forms.TextInput(attrs={"class": "form-input w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30 font-mono uppercase placeholder-slate-400", "placeholder": "e.g. TRP-2026-1001"}),
            "pickup": forms.TextInput(attrs={"class": "form-input w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30 placeholder-slate-400", "placeholder": "Source location / Warehouse"}),
            "destination": forms.TextInput(attrs={"class": "form-input w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30 placeholder-slate-400", "placeholder": "Destination location / Client Hub"}),
            "vehicle": forms.Select(attrs={"class": "form-select w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30"}),
            "driver": forms.Select(attrs={"class": "form-select w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30"}),
            "cargo": forms.TextInput(attrs={"class": "form-input w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30 placeholder-slate-400", "placeholder": "e.g. Electronics / Auto Parts"}),
            "cargo_weight": forms.NumberInput(attrs={"class": "form-input w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30 placeholder-slate-400", "placeholder": "Weight in KG", "min": "1"}),
            "planned_distance": forms.NumberInput(attrs={"class": "form-input w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30 placeholder-slate-400", "placeholder": "Distance in KM", "min": "1"}),
            "departure_time": forms.DateTimeInput(format="%Y-%m-%dT%H:%M", attrs={"class": "form-input w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30", "type": "datetime-local"}),
            "remarks": forms.Textarea(attrs={"class": "form-textarea w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30 placeholder-slate-400", "rows": "3", "placeholder": "Optional dispatch notes, route constraints, or client instructions"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter available vehicles
        available_vehicles = Vehicle.objects.filter(is_active=True, status="available")
        if self.instance and self.instance.pk and self.instance.vehicle:
            available_vehicles = available_vehicles | Vehicle.objects.filter(pk=self.instance.vehicle.pk)
        self.fields["vehicle"].queryset = available_vehicles.distinct()

        # Filter available drivers with unexpired licenses
        today = timezone.now().date()
        available_drivers = Driver.objects.filter(is_active=True, status="available", license_expiry__gte=today)
        if self.instance and self.instance.pk and self.instance.driver:
            available_drivers = available_drivers | Driver.objects.filter(pk=self.instance.driver.pk)
        self.fields["driver"].queryset = available_drivers.distinct()

    def clean_trip_number(self):
        tn = self.cleaned_data.get("trip_number", "").strip().upper()
        qs = Trip.objects.filter(trip_number=tn)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("A trip with this trip number already exists.")
        return tn

    def clean(self):
        cleaned_data = super().clean()
        vehicle = cleaned_data.get("vehicle")
        driver = cleaned_data.get("driver")
        cargo_weight = cleaned_data.get("cargo_weight")

        # Business Rule 1: Cargo weight must not exceed Vehicle capacity
        if vehicle and cargo_weight is not None:
            if cargo_weight > vehicle.capacity:
                self.add_error(
                    "cargo_weight",
                    f"Cargo weight ({cargo_weight} KG) exceeds vehicle capacity ({vehicle.capacity} KG for {vehicle.registration_number})."
                )

        # Business Rule 2: Vehicle availability & insurance validation
        if vehicle:
            if not vehicle.is_active or vehicle.status in ["retired", "in_shop", "on_trip"]:
                if not (self.instance and self.instance.pk and self.instance.vehicle == vehicle):
                    self.add_error(
                        "vehicle",
                        f"Vehicle {vehicle.registration_number} is currently '{vehicle.get_status_display()}' and cannot be assigned."
                    )
            elif vehicle.insurance_expiry < timezone.now().date():
                if not (self.instance and self.instance.pk and self.instance.vehicle == vehicle):
                    self.add_error(
                        "vehicle",
                        f"Vehicle {vehicle.registration_number}'s insurance expired on {vehicle.insurance_expiry}. Cannot assign to trip."
                    )

        # Business Rule 3: Driver availability and license validation
        if driver:
            today = timezone.now().date()
            if driver.is_license_expired:
                if not (self.instance and self.instance.pk and self.instance.driver == driver):
                    self.add_error(
                        "driver",
                        f"Driver {driver.name}'s license ({driver.license_number}) expired on {driver.license_expiry}. Cannot assign to trip."
                    )
            elif not driver.is_active or driver.status in ["suspended", "on_trip", "off_duty"]:
                if not (self.instance and self.instance.pk and self.instance.driver == driver):
                    self.add_error(
                        "driver",
                        f"Driver {driver.name} is currently '{driver.get_status_display()}' and cannot be assigned."
                    )

        return cleaned_data


class TripCompleteForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = [
            "end_odometer",
            "fuel_consumed",
            "trip_revenue",
            "remarks",
        ]
        widgets = {
            "end_odometer": forms.NumberInput(attrs={"class": "form-input w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-green-600/30 placeholder-slate-400", "placeholder": "Final Odometer Reading (KM)", "min": "0"}),
            "fuel_consumed": forms.NumberInput(attrs={"class": "form-input w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-green-600/30 placeholder-slate-400", "placeholder": "Total Fuel Used (Liters)", "step": "0.01", "min": "0"}),
            "trip_revenue": forms.NumberInput(attrs={"class": "form-input w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-green-600/30 placeholder-slate-400", "placeholder": "Total Revenue (₹)", "step": "0.01", "min": "0"}),
            "remarks": forms.Textarea(attrs={"class": "form-textarea w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-green-600/30 placeholder-slate-400", "rows": "3", "placeholder": "Delivery summary, delays encountered, or toll/parking notes"}),
        }

    def clean_end_odometer(self):
        end_odo = self.cleaned_data.get("end_odometer")
        if end_odo is not None and self.instance and self.instance.start_odometer:
            if end_odo < self.instance.start_odometer:
                raise forms.ValidationError(f"Final odometer ({end_odo}) cannot be lower than start odometer ({self.instance.start_odometer}).")
        return end_odo


class MaintenanceForm(forms.ModelForm):
    class Meta:
        model = Maintenance
        fields = [
            "vehicle",
            "service_type",
            "description",
            "technician",
            "scheduled_date",
            "completed_date",
            "estimated_cost",
            "actual_cost",
            "status",
            "notes",
        ]
        widgets = {
            "vehicle": forms.Select(attrs={"class": "form-select w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30"}),
            "service_type": forms.TextInput(attrs={"class": "form-input w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30 placeholder-slate-400", "placeholder": "e.g. Engine Overhaul / Brake Service / Oil Change"}),
            "description": forms.Textarea(attrs={"class": "form-textarea w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30 placeholder-slate-400", "rows": "3", "placeholder": "Detailed breakdown or scheduled inspection items"}),
            "technician": forms.TextInput(attrs={"class": "form-input w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30 placeholder-slate-400", "placeholder": "e.g. Ashok Sharma / Depot Workshop Team"}),
            "scheduled_date": forms.DateInput(format="%Y-%m-%d", attrs={"class": "form-input w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30", "type": "date"}),
            "completed_date": forms.DateInput(format="%Y-%m-%d", attrs={"class": "form-input w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30", "type": "date"}),
            "estimated_cost": forms.NumberInput(attrs={"class": "form-input w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30 placeholder-slate-400", "placeholder": "Estimated Cost (₹)", "step": "0.01", "min": "0"}),
            "actual_cost": forms.NumberInput(attrs={"class": "form-input w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30 placeholder-slate-400", "placeholder": "Actual Billed Cost (₹)", "step": "0.01", "min": "0"}),
            "status": forms.Select(attrs={"class": "form-select w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30"}),
            "notes": forms.Textarea(attrs={"class": "form-textarea w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30 placeholder-slate-400", "rows": "2", "placeholder": "Optional technician remarks, parts replaced, or warranty notes"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Exclude Retired and Deleted vehicles
        available_vehicles = Vehicle.objects.filter(is_active=True).exclude(status="retired")
        if self.instance and self.instance.pk and self.instance.vehicle:
            available_vehicles = available_vehicles | Vehicle.objects.filter(pk=self.instance.vehicle.pk)
        self.fields["vehicle"].queryset = available_vehicles.distinct()

    def clean(self):
        cleaned_data = super().clean()
        vehicle = cleaned_data.get("vehicle")
        status = cleaned_data.get("status")

        if vehicle and vehicle.status == "on_trip":
            if not (self.instance and self.instance.pk and self.instance.vehicle == vehicle and self.instance.status == status):
                self.add_error("vehicle", f"Vehicle {vehicle.registration_number} is currently On Trip and cannot enter maintenance.")

        return cleaned_data


class FuelLogForm(forms.ModelForm):
    class Meta:
        model = FuelLog
        fields = [
            "vehicle",
            "trip",
            "fuel_date",
            "odometer",
            "liters",
            "cost",
            "fuel_type",
            "vendor",
        ]
        widgets = {
            "vehicle": forms.Select(attrs={"class": "form-select w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30"}),
            "trip": forms.Select(attrs={"class": "form-select w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30"}),
            "fuel_date": forms.DateInput(format="%Y-%m-%d", attrs={"class": "form-input w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30", "type": "date"}),
            "odometer": forms.NumberInput(attrs={"class": "form-input w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30 placeholder-slate-400", "placeholder": "Current Odometer Reading (KM)", "min": "0"}),
            "liters": forms.NumberInput(attrs={"class": "form-input w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30 placeholder-slate-400", "placeholder": "Liters Fueled", "step": "0.01", "min": "0.01"}),
            "cost": forms.NumberInput(attrs={"class": "form-input w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30 placeholder-slate-400", "placeholder": "Total Cost (₹)", "step": "0.01", "min": "0"}),
            "fuel_type": forms.Select(attrs={"class": "form-select w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30"}),
            "vendor": forms.TextInput(attrs={"class": "form-input w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30 placeholder-slate-400", "placeholder": "e.g. IndianOil Highway Station #41"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["vehicle"].queryset = Vehicle.objects.filter(is_active=True)
        self.fields["trip"].queryset = Trip.objects.filter(is_active=True)
        self.fields["trip"].required = False

    def clean(self):
        cleaned_data = super().clean()
        vehicle = cleaned_data.get("vehicle")
        trip = cleaned_data.get("trip")
        odometer = cleaned_data.get("odometer")

        if trip and vehicle and trip.vehicle != vehicle:
            self.add_error("trip", f"Selected trip {trip.trip_number} belongs to vehicle {trip.vehicle.registration_number}, not {vehicle.registration_number}.")

        if vehicle and odometer is not None and not self.instance.pk:
            if odometer < vehicle.odometer:
                self.add_error("odometer", f"Odometer reading ({odometer}) cannot be lower than current vehicle odometer ({vehicle.odometer} KM).")

        return cleaned_data


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = [
            "vehicle",
            "trip",
            "expense_type",
            "amount",
            "expense_date",
            "remarks",
        ]
        widgets = {
            "vehicle": forms.Select(attrs={"class": "form-select w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30"}),
            "trip": forms.Select(attrs={"class": "form-select w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30"}),
            "expense_type": forms.Select(attrs={"class": "form-select w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30"}),
            "amount": forms.NumberInput(attrs={"class": "form-input w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30 placeholder-slate-400", "placeholder": "Expense Amount (₹)", "step": "0.01", "min": "0"}),
            "expense_date": forms.DateInput(format="%Y-%m-%d", attrs={"class": "form-input w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30", "type": "date"}),
            "remarks": forms.Textarea(attrs={"class": "form-textarea w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-[#2563EB]/30 placeholder-slate-400", "rows": "3", "placeholder": "Detailed description, toll receipt ID, repair shop notes or vendor"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["vehicle"].queryset = Vehicle.objects.filter(is_active=True)
        self.fields["trip"].queryset = Trip.objects.filter(is_active=True)
        self.fields["trip"].required = False

    def clean(self):
        cleaned_data = super().clean()
        vehicle = cleaned_data.get("vehicle")
        trip = cleaned_data.get("trip")

        if trip and vehicle and trip.vehicle != vehicle:
            self.add_error("trip", f"Selected trip {trip.trip_number} belongs to vehicle {trip.vehicle.registration_number}, not {vehicle.registration_number}.")

        return cleaned_data
