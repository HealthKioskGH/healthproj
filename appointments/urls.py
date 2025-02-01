from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'appointments'

urlpatterns = [
    # Regular views
    path('list/', views.AppointmentListView.as_view(), name='list'),
    path('book/', views.BookAppointmentView.as_view(), name='book'),
    path('cancel/<int:pk>/', views.CancelAppointmentView.as_view(), name='cancel'),
    path('delete/<int:pk>/', views.DeleteAppointmentView.as_view(), name='delete'),
    path('reschedule/<int:pk>/', views.RescheduleAppointmentView.as_view(), name='reschedule'),
    path('complete/<int:pk>/', views.CompleteAppointmentView.as_view(), name='complete'),
    
    # API endpoints
    path('api/time-slots/', views.TimeSlotAPIView.as_view(), name='time_slots'),
    path('api/', include(DefaultRouter().urls)),
] 