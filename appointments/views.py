from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.views.generic import ListView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from datetime import datetime, timedelta
import pytz
from notifications.utils import (
    notify_appointment_updated, 
    notify_appointment_created,
    notify_appointment_cancelled
)

from .models import Appointment, DoctorSchedule, TimeSlot
from .serializers import AppointmentSerializer, DoctorScheduleSerializer, TimeSlotSerializer

User = get_user_model()

def parse_time_with_ampm(time_str):
    """Parse time string in 12-hour format with AM/PM and convert to GMT."""
    try:
        # Parse the time string
        time_obj = datetime.strptime(time_str, "%I:%M %p").time()
    except ValueError:
        try:
            # Fallback to 24-hour format if 12-hour parsing fails
            time_obj = datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            raise ValueError("Invalid time format. Please use either '12-hour (e.g., 2:30 PM)' or '24-hour (e.g., 14:30)' format.")
    
    return time_obj

def convert_to_gmt(date_obj, time_obj, user_timezone='UTC'):
    """Convert local datetime to GMT."""
    local_tz = pytz.timezone(user_timezone)
    local_dt = datetime.combine(date_obj, time_obj)
    local_dt = local_tz.localize(local_dt)
    return local_dt.astimezone(pytz.UTC)

class AppointmentViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    
    def get_queryset(self):
        if self.request.user.is_patient():
            return Appointment.objects.filter(patient=self.request.user)
        else:
            return Appointment.objects.filter(doctor=self.request.user)

class DoctorScheduleViewSet(viewsets.ModelViewSet):
    serializer_class = DoctorScheduleSerializer
    queryset = DoctorSchedule.objects.all()

class TimeSlotViewSet(viewsets.ModelViewSet):
    serializer_class = TimeSlotSerializer
    queryset = TimeSlot.objects.all()

class AppointmentListView(LoginRequiredMixin, ListView):
    model = Appointment
    template_name = 'appointments/list.html'
    context_object_name = 'appointments'

    def get_queryset(self):
        # Get the filter from query parameters, default to 'upcoming'
        current_filter = self.request.GET.get('filter', 'upcoming')
        
        # Base queryset based on user type
        if self.request.user.is_doctor():
            queryset = Appointment.objects.filter(doctor=self.request.user)
        else:
            queryset = Appointment.objects.filter(patient=self.request.user)
            
        # Apply filter
        now = timezone.now()
        ten_minutes_ago = now - timezone.timedelta(minutes=10)
        
        if current_filter == 'upcoming':
            queryset = queryset.filter(
                appointment_date__gt=ten_minutes_ago,
                status='scheduled'
            )
        elif current_filter == 'completed':
            queryset = queryset.filter(status='completed')
        elif current_filter == 'cancelled':
            queryset = queryset.filter(status='cancelled')
        elif current_filter == 'past':
            queryset = queryset.filter(
                appointment_date__lte=ten_minutes_ago,
                status='scheduled'
            )
            
        return queryset.order_by('appointment_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_filter'] = self.request.GET.get('filter', 'upcoming')
        context['today'] = timezone.now().date()
        context['timezone'] = 'GMT'  # Add timezone info to context
        
        # Add past appointments count for doctors
        if self.request.user.is_doctor():
            ten_minutes_ago = timezone.now() - timezone.timedelta(minutes=10)
            context['past_appointments_count'] = Appointment.objects.filter(
                doctor=self.request.user,
                appointment_date__lte=ten_minutes_ago,
                status='scheduled'
            ).count()
            
        return context

class BookAppointmentView(LoginRequiredMixin, View):
    def post(self, request):
        if not request.user.is_patient():
            messages.error(request, 'Only patients can book appointments.')
            return redirect('appointments:list')
        
        appointment_date = request.POST.get('appointment_date')
        appointment_time = request.POST.get('appointment_time')
        reason = request.POST.get('reason')
        
        if not all([appointment_date, appointment_time, reason]):
            messages.error(request, 'Please fill in all required fields.')
            return redirect('appointments:list')
        
        doctor = request.user.assigned_doctor
        if not doctor:
            messages.error(request, 'You need to have an assigned doctor to book appointments.')
            return redirect('appointments:list')
        
        try:
            # Parse date and time
            date_obj = datetime.strptime(appointment_date, "%Y-%m-%d").date()
            time_obj = parse_time_with_ampm(appointment_time)
            
            # Convert to GMT
            appointment_datetime = convert_to_gmt(date_obj, time_obj)
            
            # Create appointment
            appointment = Appointment.objects.create(
                patient=request.user,
                doctor=doctor,
                appointment_date=appointment_datetime,
                reason=reason,
                status='scheduled',
                last_modified_by=request.user
            )
            
            # Create notification for doctor
            notify_appointment_created(appointment)
            
            messages.success(request, f'Appointment booked successfully for {appointment_datetime.strftime("%B %d, %Y at %I:%M %p")} GMT')
            
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, 'An error occurred while booking the appointment.')
        
        return redirect('appointments:list')

class CancelAppointmentView(LoginRequiredMixin, View):
    def post(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk)
        
        # Check basic permissions
        if appointment.patient != request.user and appointment.doctor != request.user:
            messages.error(request, 'You do not have permission to cancel this appointment.')
            return redirect('appointments:list')
            
        # Check if the appointment can be cancelled
        if not appointment.can_be_cancelled():
            messages.error(request, 'This appointment cannot be cancelled.')
            return redirect('appointments:list')
            
        # Additional permission checks for past and completed appointments
        is_past = appointment.appointment_date <= timezone.now()
        if (is_past or appointment.status == 'completed') and not request.user.is_doctor():
            messages.error(request, 'Only doctors can cancel past or completed appointments.')
            return redirect('appointments:list')
            
        # Store the previous status for notification message
        was_completed = appointment.status == 'completed'
        
        # Cancel the appointment
        appointment.status = 'cancelled'
        appointment.last_modified_by = request.user
        appointment.save()

        # Create notification for the other party
        notification_message = (
            f'Your {"completed " if was_completed else ""}appointment '
            f'{"with" if request.user.is_doctor() else "by"} '
            f'{"Dr. " if request.user.is_doctor() else ""}{request.user.get_full_name()} '
            f'has been cancelled.'
        )
        
        notify_appointment_cancelled(appointment, cancelled_by=request.user)

        messages.success(request, 'Appointment cancelled successfully.')
        return redirect('appointments:list')

class DeleteAppointmentView(LoginRequiredMixin, View):
    def post(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk)
        if (appointment.patient == request.user or appointment.doctor == request.user) and appointment.status == 'cancelled':
            appointment.delete()
            messages.success(request, 'Appointment deleted successfully.')
        else:
            messages.error(request, 'You can only delete cancelled appointments.')
        return redirect('appointments:list')

class RescheduleAppointmentView(LoginRequiredMixin, View):
    def post(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk)
        if appointment.patient == request.user or appointment.doctor == request.user:
            try:
                new_date = request.POST.get('new_date')
                new_time = request.POST.get('new_time')
                
                if not all([new_date, new_time]):
                    messages.error(request, 'Please provide both date and time.')
                    return redirect('appointments:list')
                
                # Parse date and time
                date_obj = datetime.strptime(new_date, "%Y-%m-%d").date()
                time_obj = parse_time_with_ampm(new_time)
                
                # Convert to GMT
                new_datetime = convert_to_gmt(date_obj, time_obj)
                
                # Update the appointment
                appointment.appointment_date = new_datetime
                appointment.last_modified_by = request.user
                appointment.save()

                # Create notification for the other party
                notify_appointment_updated(appointment)
                
                messages.success(request, f'Appointment rescheduled successfully to {new_datetime.strftime("%B %d, %Y at %I:%M %p")} GMT')
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, 'An error occurred while rescheduling the appointment.')
        else:
            messages.error(request, 'You do not have permission to reschedule this appointment.')
        return redirect('appointments:list')

class TimeSlotAPIView(LoginRequiredMixin, View):
    def get(self, request):
        try:
            date = request.GET.get('date')
            doctor_id = request.GET.get('doctor')
            
            # Convert date string to datetime
            selected_date = datetime.strptime(date, "%Y-%m-%d").date()
            
            # Generate time slots (9 AM to 5 PM, 30-minute intervals)
            start_time = datetime.strptime(f"{date} 09:00", "%Y-%m-%d %H:%M")
            end_time = datetime.strptime(f"{date} 17:00", "%Y-%m-%d %H:%M")
            interval = timedelta(minutes=30)
            
            # Get booked appointments for the day
            booked_times = Appointment.objects.filter(
                doctor_id=doctor_id,
                appointment_date__date=selected_date,
                status='scheduled'
            ).values_list('appointment_date', flat=True)
            
            slots = []
            current = start_time
            while current < end_time:
                slot = current.strftime("%H:%M")
                is_booked = any(t.strftime("%H:%M") == slot for t in booked_times)
                slots.append({
                    'time': slot,
                    'is_available': not is_booked
                })
                current += interval
            
            return JsonResponse(slots, safe=False)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Invalid date format'}, status=400)

class CompleteAppointmentView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if not request.user.is_doctor():
            messages.error(request, 'Only doctors can mark appointments as complete.')
            return redirect('appointments:list')
            
        appointment = get_object_or_404(Appointment, pk=pk, doctor=request.user)
        
        # Check if appointment is in the past
        if appointment.appointment_date > timezone.now():
            messages.error(request, 'Cannot mark a future appointment as complete.')
            return redirect('appointments:list')
            
        # Check if appointment is already completed or cancelled
        if appointment.status in ['completed', 'cancelled']:
            messages.error(request, f'Appointment is already {appointment.status}.')
            return redirect('appointments:list')
            
        # Get notes from the request
        notes = request.POST.get('notes', '')
        
        # Update appointment
        appointment.status = 'completed'
        appointment.notes = notes
        appointment.last_modified_by = request.user
        appointment.save()
        
        # Create notification for patient with notes
        from notifications.models import Notification
        notification_message = f'Your appointment with Dr. {request.user.get_full_name()} has been marked as complete.'
        if notes:
            notification_message += f'\n\nDoctor\'s Notes:\n{notes}'
            
        Notification.objects.create(
            recipient=appointment.patient,
            sender=request.user,
            notification_type='appointment_completed',
            title='Appointment Completed',
            message=notification_message,
            link=f'/appointments/{appointment.id}/'
        )
        
        messages.success(request, 'Appointment marked as complete successfully.')
        
        # If this is an AJAX request, return JSON response
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': 'Appointment marked as complete successfully.'
            })
            
        return redirect('appointments:list')

class MarkAppointmentIncompleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if not request.user.is_doctor():
            messages.error(request, 'Only doctors can mark appointments as incomplete.')
            return redirect('appointments:list')
            
        appointment = get_object_or_404(Appointment, pk=pk, doctor=request.user)
        
        if not appointment.can_be_marked_incomplete():
            messages.error(request, 'This appointment cannot be marked as incomplete.')
            return redirect('appointments:list')
        
        # Update appointment status back to scheduled
        appointment.status = 'scheduled'
        appointment.last_modified_by = request.user
        appointment.save()
        
        # Create notification for patient
        from notifications.models import Notification
        Notification.objects.create(
            recipient=appointment.patient,
            sender=request.user,
            notification_type='appointment_status_changed',
            title='Appointment Status Updated',
            message=f'Your completed appointment with Dr. {request.user.get_full_name()} has been marked as incomplete and needs to be rescheduled.',
            link=f'/appointments/{appointment.id}/'
        )
        
        messages.success(request, 'Appointment marked as incomplete successfully.')
        return redirect('appointments:list')