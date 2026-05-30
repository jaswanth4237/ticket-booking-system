from django.core.management.base import BaseCommand
from tickets.models import Event

class Command(BaseCommand):
    help = 'Seed initial data for the ticket system'

    def handle(self, *args, **options):
        # Requirement 2: Seed data with id=1, total_seats=30
        event, created = Event.objects.get_or_create(
            id=1,
            defaults={
                'name': 'Tech Conference 2024',
                'total_seats': 30,
                'booked_seats': 0,
                'version': 0
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Successfully seeded event "Tech Conference 2024"'))
        else:
            # Reset for fresh testing if already exists
            event.booked_seats = 0
            event.version = 0
            event.save()
            event.bookings.all().delete()
            self.stdout.write(self.style.SUCCESS('Reset event "Tech Conference 2024"'))
