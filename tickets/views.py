import time
import logging
from django.http import JsonResponse
from django.db import transaction, models
from django.views.decorators.csrf import csrf_exempt
from .models import Event, Booking

logger = logging.getLogger(__name__)

def send_confirmation_email(event_id):
    # Requirement 7: The registered function must log a specific message to the container's standard output.
    print(f"CONFIRMATION: Booking successful for event {event_id}.")

@csrf_exempt
def book_vulnerable(request, event_id):
    if request.method == 'POST':
        try:
            event = Event.objects.get(id=event_id)
            if event.booked_seats < event.total_seats:
                # Simulate processing time to make race condition more likely
                time.sleep(0.1)
                event.booked_seats += 1
                Booking.objects.create(event=event, user_name='Vulnerable User')
                event.save()
                return JsonResponse({'status': 'success'}, status=201)
            else:
                return JsonResponse({'status': 'error', 'message': 'No seats available'}, status=400)
        except Event.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Event not found'}, status=404)
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

@csrf_exempt
def book_pessimistic(request, event_id):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Acquire a lock on the event row
                event = Event.objects.select_for_update().get(id=event_id)
                if event.booked_seats < event.total_seats:
                    event.booked_seats += 1
                    Booking.objects.create(event=event, user_name='Pessimistic User')
                    event.save()
                    
                    # Requirement 7: Use transaction.on_commit
                    transaction.on_commit(lambda: send_confirmation_email(event.id))
                    
                    return JsonResponse({'status': 'success'}, status=201)
                else:
                    return JsonResponse({'status': 'error', 'message': 'No seats available'}, status=400)
        except Event.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Event not found'}, status=404)
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

@csrf_exempt
def book_pessimistic_fail(request, event_id):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                event = Event.objects.select_for_update().get(id=event_id)
                if event.booked_seats < event.total_seats:
                    event.booked_seats += 1
                    Booking.objects.create(event=event, user_name='Failing User')
                    event.save()
                    
                    # Register on_commit hook
                    transaction.on_commit(lambda: send_confirmation_email(event.id))
                    
                    # Requirement 8: Deliberately raise an exception to cause rollback
                    raise Exception("Simulating an error!")
                    
                return JsonResponse({'status': 'success'}, status=201)
        except Event.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Event not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

@csrf_exempt
def book_optimistic(request, event_id):
    if request.method == 'POST':
        try:
            # We don't use select_for_update here
            # We use an atomic update with version check
            with transaction.atomic():
                event = Event.objects.get(id=event_id)
                if event.booked_seats < event.total_seats:
                    # Requirement 6: UPDATE ... WHERE id = X AND version = Y
                    updated_rows = Event.objects.filter(
                        id=event_id, 
                        version=event.version
                    ).update(
                        booked_seats=models.F('booked_seats') + 1,
                        version=models.F('version') + 1
                    )
                    
                    if updated_rows == 0:
                        # Requirement 6: Conflict response (409)
                        return JsonResponse({'status': 'error', 'message': 'Conflict, please retry'}, status=409)
                    
                    Booking.objects.create(event=event, user_name='Optimistic User')
                    return JsonResponse({'status': 'success'}, status=201)
                else:
                    return JsonResponse({'status': 'error', 'message': 'No seats available'}, status=400)
        except Event.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Event not found'}, status=404)
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def get_event_status(request, event_id):
    try:
        event = Event.objects.get(id=event_id)
        return JsonResponse({
            'id': event.id,
            'name': event.name,
            'total_seats': event.total_seats,
            'booked_seats': event.booked_seats,
            'version': event.version
        })
    except Event.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)

@csrf_exempt
def reset_db(request, event_id):
    if request.method == 'POST':
        try:
            event = Event.objects.get(id=event_id)
            event.booked_seats = 0
            event.version = 0
            event.save()
            event.bookings.all().delete()
            return JsonResponse({'status': 'success'})
        except Event.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Event not found'}, status=404)
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
