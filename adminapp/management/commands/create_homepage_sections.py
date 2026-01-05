# Create file: management/commands/create_homepage_sections.py

from django.core.management.base import BaseCommand
from adminapp.models import HomepageSection

class Command(BaseCommand):
    help = 'Creates initial homepage sections'

    def handle(self, *args, **kwargs):
        sections = [
            {'name': 'Banner Products', 'section_type': 'banner', 'display_order': 1},
            {'name': 'Featured Products', 'section_type': 'featured', 'display_order': 2},
            {'name': 'Deals of the Day', 'section_type': 'deals', 'display_order': 3},
            {'name': 'New Arrivals', 'section_type': 'new_arrival', 'display_order': 4},
            {'name': 'Best Sellers', 'section_type': 'best_seller', 'display_order': 5},
        ]
        
        for section_data in sections:
            section, created = HomepageSection.objects.get_or_create(
                section_type=section_data['section_type'],
                defaults=section_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created section: {section.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Section already exists: {section.name}'))