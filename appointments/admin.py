from django.contrib import admin
from .models import Appointment, DoctorSchedule, TimeSlot

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'appointment_date', 'status', 'created_at')
    list_filter = ('status', 'appointment_date', 'created_at')
    search_fields = ('patient__username', 'doctor__username', 'reason')

@admin.register(DoctorSchedule)
class DoctorScheduleAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'day_of_week', 'start_time', 'end_time', 'is_available')
    list_filter = ('doctor', 'day_of_week', 'is_available')
    search_fields = ('doctor__username',)

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'start_time', 'end_time', 'is_booked')
    list_filter = ('doctor', 'is_booked', 'start_time')
    search_fields = ('doctor__username',) 