from django.urls import path
from . import views

urlpatterns = [
    path('events/<int:event_id>/book_vulnerable/', views.book_vulnerable, name='book_vulnerable'),
    path('events/<int:event_id>/book_pessimistic/', views.book_pessimistic, name='book_pessimistic'),
    path('events/<int:event_id>/book_pessimistic_fail/', views.book_pessimistic_fail, name='book_pessimistic_fail'),
    path('events/<int:event_id>/book_optimistic/', views.book_optimistic, name='book_optimistic'),
    path('events/<int:event_id>/status/', views.get_event_status, name='event_status'),
    path('events/<int:event_id>/reset/', views.reset_db, name='reset_db'),
]
