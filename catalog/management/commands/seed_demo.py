"""EN-02: `python manage.py seed_demo` - create demo regions, species and accounts.

Safe to run repeatedly: anything that already exists is left alone.
"""

import os
from decimal import Decimal

from django.core.management.base import BaseCommand

from accounts.models import User
from catalog import seed_data
from catalog.models import Species, SpeciesRegion
from growprofiles.models import GrowProfile, Region

# Demo/test password only. In production set DEMO_PASSWORD to something private.
DEMO_PASSWORD = os.environ.get("DEMO_PASSWORD", "Basera-demo-2026")

# Price range (min, spread) and stock by plant type, spread deterministically over the list.
PRICE_BANDS = {"Tree": (500, 2000), "Shrub": (300, 700), "Herb": (150, 250), "Grass": (150, 250)}


class Command(BaseCommand):
    help = "Create demo regions, species and the admin/seller/customer demo accounts (idempotent)."

    def handle(self, *args, **options):
        self.create_accounts()
        regions = self.create_regions()
        seller = User.objects.get(email="seller@basera.test")
        self.create_species(seller, regions)
        self.create_sample_profile(regions)
        self.stdout.write(self.style.SUCCESS("Seed data is ready."))

    def create_accounts(self):
        """Create each demo account only if it is missing, and print its password when created."""
        accounts = [
            ("admin@basera.test", "Demo", "Admin", User.Role.CUSTOMER, True),
            ("seller@basera.test", "Demo", "Seller", User.Role.SELLER, False),
            ("customer@basera.test", "Demo", "Customer", User.Role.CUSTOMER, False),
        ]
        for email, first, last, role, is_admin in accounts:
            if User.objects.filter(email=email).exists():
                self.stdout.write(f"Account {email} already exists.")
                continue
            make = User.objects.create_superuser if is_admin else User.objects.create_user
            make(email, DEMO_PASSWORD, first_name=first, last_name=last, role=role)
            self.stdout.write(f"Created {email}  (demo password: {DEMO_PASSWORD})")

    def create_regions(self):
        regions = {}
        for code, (name, description) in seed_data.REGIONS.items():
            regions[code], _ = Region.objects.get_or_create(name=name, defaults={"description": description})
        return regions

    def create_species(self, seller, regions):
        created = 0
        for index, row in enumerate(seed_data.SPECIES):
            (common, scientific, region_codes, sun, water, soil, setting, plant_type,
             purposes, invasive, description, benefit) = row
            low, spread = PRICE_BANDS[plant_type]
            species, was_created = Species.objects.get_or_create(
                seller=seller,
                scientific_name=scientific,
                defaults={
                    "common_name": common,
                    "description": description,
                    "price": Decimal(low + (index * 137) % spread),  # whole rupees, Rs 150 - 2,500
                    "stock": 5 + (index * 7) % 46,  # 5 - 50
                    "sunlight": seed_data.SUN[sun],
                    "water": seed_data.WATER[water],
                    "soil": seed_data.SOIL[soil],
                    "setting": seed_data.SETTING[setting],
                    "plant_type": seed_data.TYPE[plant_type],
                    "purposes": ",".join(purposes.split()),
                    "ecological_benefit": benefit,
                    "is_invasive": invasive,
                },
            )
            if was_created:
                created += 1
                for code in region_codes.split():
                    SpeciesRegion.objects.create(species=species, region=regions[code])
        self.stdout.write(f"Species: {created} created, {len(seed_data.SPECIES) - created} already present.")

    def create_sample_profile(self, regions):
        """One sample grow profile for the demo customer (created only if they have none)."""
        customer = User.objects.get(email="customer@basera.test")
        if GrowProfile.objects.filter(customer=customer).exists():
            return
        GrowProfile.objects.create(
            customer=customer, name="Backyard", region=regions["PP"], space_type="OUTDOOR",
            sunlight="FULL_SUN", soil="LOAM", water="MEDIUM", purpose="SHADE_COOLING",
        )
        self.stdout.write("Created sample grow profile 'Backyard' for the demo customer.")
