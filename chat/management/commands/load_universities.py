"""
Django management command to load university data from JSON file into database.

This command reads the data.json file and populates the University model.
Run with: python manage.py load_universities
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from chat.models import University
import json
import os


class Command(BaseCommand):
    help = 'Load university data from data.json into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='data.json',
            help='Path to the JSON file containing university data',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing university data before loading',
        )

    def handle(self, *args, **options):
        json_file = options['file']

        # Use absolute path
        if not os.path.isabs(json_file):
            json_file = os.path.join(settings.BASE_DIR, json_file)

        if not os.path.exists(json_file):
            self.stdout.write(
                self.style.ERROR(f'File not found: {json_file}')
            )
            return

        # Clear existing data if requested
        if options['clear']:
            self.stdout.write('Clearing existing university data...')
            University.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS('Existing data cleared.')
            )

        # Load JSON data
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                universities_data = json.load(f)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error reading JSON file: {e}')
            )
            return

        # Process and save universities
        created_count = 0
        updated_count = 0

        for uni_data in universities_data:
            try:
                # Extract data with defaults
                university_name = uni_data.get('university_name', '')
                if not university_name:
                    continue

                # Try to get existing university or create new one
                university, created = University.objects.get_or_create(
                    university_name=university_name,
                    defaults={
                        'country': uni_data.get('country', ''),
                        'city': uni_data.get('city', ''),
                        'tuition': uni_data.get('tuition', ''),
                        'ielts_requirement': self._parse_float(uni_data.get('ielts')),
                        'toefl_requirement': self._parse_int(uni_data.get('toefl')),
                        'ranking': uni_data.get('ranking', ''),
                        'programs': uni_data.get('programs', []),
                        'notes': uni_data.get('notes', ''),
                        'affordability': uni_data.get('affordability', ''),
                        'region': uni_data.get('region', ''),
                        'name_variations': uni_data.get('name_variations', []),
                        'program_categories': uni_data.get('program_categories', []),
                        'searchable_text': uni_data.get('searchable_text', ''),
                        'apply_url': uni_data.get('apply_url', ''),
                    }
                )

                if created:
                    created_count += 1
                else:
                    # Update existing university
                    university.country = uni_data.get('country', university.country)
                    university.city = uni_data.get('city', university.city)
                    university.tuition = uni_data.get('tuition', university.tuition)
                    university.ielts_requirement = self._parse_float(uni_data.get('ielts')) or university.ielts_requirement
                    university.toefl_requirement = self._parse_int(uni_data.get('toefl')) or university.toefl_requirement
                    university.ranking = uni_data.get('ranking', university.ranking)
                    university.programs = uni_data.get('programs', university.programs)
                    university.notes = uni_data.get('notes', university.notes)
                    university.affordability = uni_data.get('affordability', university.affordability)
                    university.region = uni_data.get('region', university.region)
                    university.name_variations = uni_data.get('name_variations', university.name_variations)
                    university.program_categories = uni_data.get('program_categories', university.program_categories)
                    university.searchable_text = uni_data.get('searchable_text', university.searchable_text)
                    university.apply_url = uni_data.get('apply_url', '') or university.apply_url or ''
                    university.save()
                    updated_count += 1

                # Progress indicator
                if (created_count + updated_count) % 50 == 0:
                    self.stdout.write(f'Processed {created_count + updated_count} universities...')

            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Error processing university {university_name}: {e}')
                )
                continue

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully loaded university data:\n'
                f'  - Created: {created_count} new universities\n'
                f'  - Updated: {updated_count} existing universities\n'
                f'  - Total: {University.objects.count()} universities in database'
            )
        )

    def _parse_float(self, value):
        """Safely parse float value"""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _parse_int(self, value):
        """Safely parse integer value"""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None