from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from Time_Banking.models import Tag, Category

class Command(BaseCommand):
    help = 'Load tags from a text file'

    def add_arguments(self, parser):
        parser.add_argument('filepath', type=str, help='Path to the text file containing tags.')

    def handle(self, *args, **options):
        filepath = options['filepath']
        try:
            with open(filepath, 'r') as f:
                lines = [line.strip() for line in f if line.strip()]

            # Validate all lines before starting the transaction
            valid_categories = [choice[0] for choice in Category.choices]

            parsed_data = []
            for line in lines:
                if ':' not in line:
                    raise CommandError(f"Invalid format in line: '{line}'. Expected 'CATEGORY: TAG_NAME'.")
                
                # Skip comments in the file
                if line.startswith('#'):
                    continue

                category_code, tag_name = line.split(':', 1)
                category_code = category_code.strip()
                tag_name = tag_name.strip()

                if category_code not in valid_categories:
                    raise CommandError(f"Invalid category code '{category_code}' in line: '{line}'.")

                parsed_data.append((category_code, tag_name))

            # If all validation passed, insert in a single transaction
            with transaction.atomic():
                for category_code, tag_name in parsed_data:
                    Tag.objects.get_or_create(category=category_code, name=tag_name)

            self.stdout.write(self.style.SUCCESS("Tags loaded successfully!"))

        except FileNotFoundError:
            raise CommandError(f"The file {filepath} does not exist.")
