import datetime
import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from transport.models import Vehicle, Driver, Trip, Maintenance, FuelLog, Expense, VehicleDocument, Notification
from transport.utils import check_and_create_notifications

User = get_user_model()


class Command(BaseCommand):
    help = "Seed database with enterprise-grade demo data (50 Vehicles, 50 Drivers, 250 Trips, 100 Maintenance, 250 Fuel, 200 Expenses)"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Initializing TransitOps Enterprise Demo Seeder (High-Volume)..."))

        # 1. Seed Custom Users & RBAC Roles
        users_data = [
            {"username": "admin", "email": "admin@transitops.erp", "role": "admin", "first_name": "Super", "last_name": "Admin", "is_superuser": True, "is_staff": True},
            {"username": "fleet_mgr", "email": "fleet@transitops.erp", "role": "fleet_manager", "first_name": "Vikram", "last_name": "Singhania", "is_superuser": False, "is_staff": True},
            {"username": "dispatcher", "email": "dispatch@transitops.erp", "role": "dispatcher", "first_name": "Suresh", "last_name": "Patel", "is_superuser": False, "is_staff": True},
            {"username": "safety_officer", "email": "safety@transitops.erp", "role": "safety_officer", "first_name": "Anjali", "last_name": "Deshmukh", "is_superuser": False, "is_staff": True},
            {"username": "finance_exec", "email": "finance@transitops.erp", "role": "finance", "first_name": "Rohan", "last_name": "Mehta", "is_superuser": False, "is_staff": True},
        ]

        for udata in users_data:
            user, created = User.objects.get_or_create(username=udata["username"], defaults={
                "email": udata["email"],
                "role": udata["role"],
                "first_name": udata["first_name"],
                "last_name": udata["last_name"],
                "is_superuser": udata["is_superuser"],
                "is_staff": udata["is_staff"]
            })
            if created or not user.check_password("admin123"):
                user.set_password("admin123")
                user.role = udata["role"]
                user.save()
                self.stdout.write(f"  [USER] Verified user: {user.username} ({user.get_role_display()})")

        random.seed(2026)
        today = timezone.now().date()
        now = timezone.now()

        # 2. Seed 50 Vehicles
        vehicle_brands = [
            ("Volvo FH16 540 Tractor", "truck", "diesel", 40000, 6500000),
            ("Tata Prima 5530.S", "truck", "diesel", 35000, 4800000),
            ("BharatBenz 5528TT", "truck", "diesel", 38000, 5200000),
            ("Ashok Leyland 4825", "truck", "diesel", 30000, 4200000),
            ("Mahindra Blazo X 49", "truck", "diesel", 34000, 4500000),
            ("Eicher Pro 6048", "truck", "diesel", 32000, 3900000),
            ("Tata Signa 4825.TK", "truck", "diesel", 32000, 4100000),
            ("Force Traveler Staff Van", "van", "diesel", 1800, 1800000),
            ("Mahindra Bolero Maxi Truck", "pickup", "cng", 1500, 850000),
            ("Volvo 9400 Intercity Bus", "bus", "diesel", 12000, 9500000),
            ("Scania G410 Heavy Tipper", "truck", "diesel", 38000, 7200000),
            ("Tata LPT 1918 Cowl", "truck", "diesel", 19000, 2600000),
            ("Ashok Leyland Dost+", "pickup", "diesel", 1475, 780000),
            ("Eicher Pro 2049", "truck", "cng", 4900, 1450000),
            ("Mahindra Furio 16", "truck", "diesel", 16000, 2400000),
        ]

        states = ["MH", "DL", "KA", "GJ", "TN", "UP", "HR", "WB", "PB", "RJ"]
        hubs = ["Mumbai Logistics Hub", "Delhi Okhla Depot", "Bangalore Peenya Yard", "Chennai Port Terminal", "Ahmedabad Sarkhej Yard", "Noida ICD Checkpost", "Gurgaon Freight Center", "Kolkata Salt Lake Depot", "Ludhiana GT Road Depot", "Jaipur Sitapura Hub"]
        statuses = ["available"] * 30 + ["on_trip"] * 15 + ["in_shop"] * 4 + ["retired"] * 1

        vehicles_list = []
        for i in range(1, 51):
            state = states[i % len(states)]
            reg = f"{state}-{(i%15)+1:02d}-HQ-{i+1000}"
            brand = vehicle_brands[i % len(vehicle_brands)]
            v_status = statuses[i - 1]
            odo = random.randint(35000, 280000) if v_status != "retired" else random.randint(350000, 500000)
            
            # Create insurance expiry (some near or expired for alerts)
            if i in [5, 12, 28]:
                ins_exp = today + datetime.timedelta(days=random.randint(-15, 15))
            else:
                ins_exp = today + datetime.timedelta(days=random.randint(60, 365))

            v, _ = Vehicle.objects.update_or_create(
                registration_number=reg,
                defaults={
                    "vehicle_name": f"{brand[0]} #{i}",
                    "vehicle_type": brand[1],
                    "fuel_type": brand[2],
                    "capacity": brand[3],
                    "odometer": odo,
                    "acquisition_cost": Decimal(str(brand[4])),
                    "status": v_status,
                    "insurance_expiry": ins_exp,
                    "current_location": hubs[i % len(hubs)],
                    "is_active": True,
                }
            )
            vehicles_list.append(v)
            
            # Create Vehicle Documents (RC, Insurance, PUC, Permit)
            for d_type in ["rc", "insurance", "puc", "permit"]:
                exp_days = random.randint(-10, 300) if (i == 7 and d_type == "puc") else random.randint(90, 700)
                VehicleDocument.objects.update_or_create(
                    vehicle=v,
                    doc_type=d_type,
                    defaults={
                        "document_number": f"DOC-{d_type.upper()}-{reg}",
                        "expiry_date": today + datetime.timedelta(days=exp_days),
                        "is_active": True
                    }
                )

        self.stdout.write(f"  [VEHICLES] Seeded 50 fleet assets along with 200 regulatory documents.")

        # 3. Seed 50 Drivers
        first_names = ["Rajesh", "Vikram", "Suresh", "Amit", "Pramod", "Gurpreet", "Manoj", "Santosh", "Deepak", "Sunil", "Ramesh", "Ajay", "Vinod", "Arun", "Sanjay", "Dinesh", "Kiran", "Naveen", "Hemant", "Yogesh"]
        last_names = ["Kumar", "Singh", "Sharma", "Patel", "Verma", "Yadav", "Tiwari", "Das", "Gupta", "Mishra", "Chauhan", "Joshi", "Thakur", "Nair", "Rao"]
        driver_statuses = ["available"] * 32 + ["on_trip"] * 15 + ["off_duty"] * 2 + ["suspended"] * 1

        drivers_list = []
        for i in range(1, 51):
            name = f"{first_names[i % len(first_names)]} {last_names[(i*3) % len(last_names)]}" if i > 8 else f"{first_names[i-1]} {last_names[i-1]}"
            lic = f"DL-201{i%10}0012{i+500}"
            d_status = driver_statuses[i - 1]
            score = random.randint(75, 100) if d_status != "suspended" else random.randint(40, 60)
            
            if i in [4, 19]:
                lic_exp = today + datetime.timedelta(days=random.randint(-10, 20))
            else:
                lic_exp = today + datetime.timedelta(days=random.randint(150, 800))

            d, _ = Driver.objects.update_or_create(
                license_number=lic,
                defaults={
                    "name": name,
                    "license_category": "Heavy Goods (HTV)" if i % 4 != 0 else "Commercial LMV/HTV",
                    "license_expiry": lic_exp,
                    "phone": f"+91 98{random.randint(10000000, 99999999)}",
                    "emergency_contact": f"+91 99{random.randint(10000000, 99999999)}",
                    "safety_score": score,
                    "status": d_status,
                    "is_active": True,
                }
            )
            drivers_list.append(d)

        self.stdout.write(f"  [DRIVERS] Seeded 50 licensed professional drivers.")

        # 4. Seed 250 Trips
        cargo_types = ["Automotive Steel Coils", "FMCG Cartons", "Auto Components", "Synthetic Yarn & Fabrics", "Industrial Machinery", "Pharmaceuticals & Medicines", "Electronic Appliances", "Heavy Spares & Lubricants", "Consumer Durables", "Fertilizer Bags"]
        trip_statuses = ["completed"] * 210 + ["dispatched"] * 25 + ["draft"] * 10 + ["cancelled"] * 5

        for i in range(1, 251):
            t_num = f"TRP-2026-{i+1000}"
            v = vehicles_list[i % 50]
            d = drivers_list[i % 50]
            status = trip_statuses[i - 1]
            
            pdist = random.randint(120, 1100)
            adist = pdist + random.randint(-15, 25) if status == "completed" else None
            cargo = cargo_types[i % len(cargo_types)]
            w = min(v.capacity - random.randint(500, 2000), int(v.capacity * 0.85))
            if w <= 0:
                w = 1500

            rev = Decimal(str(pdist * random.randint(160, 240)))
            odo_s = max(1000, v.odometer - random.randint(1000, 30000))
            odo_e = odo_s + adist if adist else None
            fuel_cons = Decimal(str(round(pdist / random.uniform(3.2, 4.5), 1))) if status == "completed" else None

            # Departure in last 180 days
            days_ago = random.randint(1, 180) if status == "completed" else random.randint(0, 2)
            dep_time = now - datetime.timedelta(days=days_ago, hours=random.randint(1, 12))
            arr_time = dep_time + datetime.timedelta(hours=round(pdist / 45, 1)) if status == "completed" else (dep_time + datetime.timedelta(hours=round(pdist/45, 1)) if status == "dispatched" and i % 7 == 0 else None)

            Trip.objects.update_or_create(
                trip_number=t_num,
                defaults={
                    "vehicle": v,
                    "driver": d,
                    "pickup": hubs[(i+2) % len(hubs)],
                    "destination": hubs[(i+5) % len(hubs)],
                    "cargo": cargo,
                    "cargo_weight": w,
                    "planned_distance": pdist,
                    "actual_distance": adist,
                    "start_odometer": odo_s,
                    "end_odometer": odo_e,
                    "fuel_consumed": fuel_cons,
                    "trip_revenue": rev,
                    "departure_time": dep_time,
                    "arrival_time": arr_time,
                    "status": status,
                    "is_active": True,
                }
            )

        self.stdout.write(f"  [TRIPS] Seeded 250 operational dispatches and logistics history.")

        # 5. Seed 100 Maintenance Logs
        service_types = ["Preventive 30,000 KM Service", "Engine Overhaul & Calibration", "Brake Lining & Suspension Flush", "Air Conditioning & Compressor Repair", "Gearbox Overhaul & Clutch Plate Check", "Turbocharger Hose Replacement", "Laser Wheel Alignment & Tyre Rotation", "Radiator Coolant Flush & Pressure Test"]
        m_statuses = ["completed"] * 85 + ["in_progress"] * 8 + ["scheduled"] * 5 + ["breakdown"] * 2

        for i in range(1, 101):
            v = vehicles_list[(i * 3) % 50]
            m_status = m_statuses[i - 1]
            stype = service_types[i % len(service_types)]
            est = Decimal(str(random.randint(12000, 85000)))
            act = est + Decimal(str(random.randint(-3000, 5000))) if m_status == "completed" else (Decimal("0") if m_status == "scheduled" else est)
            
            sdate = today - datetime.timedelta(days=random.randint(1, 160)) if m_status == "completed" else today + datetime.timedelta(days=random.randint(1, 14))
            cdate = sdate + datetime.timedelta(days=random.randint(1, 4)) if m_status == "completed" else None

            Maintenance.objects.update_or_create(
                vehicle=v,
                service_type=stype,
                scheduled_date=sdate,
                defaults={
                    "technician": f"Authorized Service Depot #{i%8 + 1}",
                    "estimated_cost": est,
                    "actual_cost": act,
                    "cost": act or est,
                    "status": m_status,
                    "completed_date": cdate,
                    "description": f"Routine maintenance and mechanical inspection for {v.registration_number}.",
                    "is_active": True,
                }
            )

        self.stdout.write(f"  [MAINTENANCE] Seeded 100 workshop and service repair orders.")

        # 6. Seed 250 Fuel Logs
        vendors = ["IndianOil Highway Plaza #412", "Bharat Petroleum NH48 Pump", "Hindustan Petroleum Express Fuel", "Reliance Jio-BP Logistics Station", "Shell Heavy Commercial Refueling"]
        for i in range(1, 251):
            v = vehicles_list[i % 50]
            fdate = today - datetime.timedelta(days=random.randint(1, 180))
            liters = Decimal(str(random.uniform(140.0, 320.0))).quantize(Decimal("0.01"))
            rate = Decimal(str(random.uniform(92.5, 96.0)))
            cost = (liters * rate).quantize(Decimal("0.01"))
            
            FuelLog.objects.update_or_create(
                vehicle=v,
                fuel_date=fdate,
                odometer=max(1000, v.odometer - random.randint(500, 40000)),
                defaults={
                    "liters": liters,
                    "cost": cost,
                    "fuel_type": v.fuel_type,
                    "vendor": vendors[i % len(vendors)],
                    "is_active": True,
                }
            )

        self.stdout.write(f"  [FUEL LOGS] Seeded 250 fuel pump transactions.")

        # 7. Seed 200 Expenses
        exp_types = ["toll", "parking", "repair", "maintenance", "miscellaneous", "other"]
        for i in range(1, 201):
            v = vehicles_list[(i * 7) % 50]
            etype = exp_types[i % len(exp_types)]
            edate = today - datetime.timedelta(days=random.randint(1, 180))
            amt = Decimal(str(random.randint(800, 15000))) if etype in ["toll", "parking"] else Decimal(str(random.randint(12000, 45000)))

            Expense.objects.update_or_create(
                vehicle=v,
                expense_type=etype,
                expense_date=edate,
                defaults={
                    "amount": amt,
                    "description": f"Operational checkpost voucher for {etype.upper()} on corridor checkpost.",
                    "remarks": f"Receipt #{i+8000} verified by finance audit.",
                    "is_active": True,
                }
            )

        self.stdout.write(f"  [EXPENSES] Seeded 200 operational accounting expense vouchers.")

        # 8. Run Notification & Reminders Scanner
        alerts_count = check_and_create_notifications()
        self.stdout.write(f"  [NOTIFICATIONS] Scanner generated {alerts_count} automated alerts.")

        self.stdout.write(self.style.SUCCESS("\n[SUCCESS] TransitOps ERP 500+ record production seeder completed!"))
