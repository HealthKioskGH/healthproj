from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Appointment(models.Model):
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rescheduled', 'Rescheduled'),
    )
    
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='patient_appointments')
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor_appointments')
    appointment_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    reason = models.TextField()
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    original_date = models.DateTimeField(null=True, blank=True)
    last_modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='modified_appointments')
    
    class Meta:
        ordering = ['-appointment_date']
        
    def __str__(self):
        return f"{self.patient.get_full_name()} - {self.doctor.get_full_name()} - {self.appointment_date}"

    def is_upcoming(self):
        # Check if appointment is more than 10 minutes past its scheduled time
        ten_minutes_after = self.appointment_date + timezone.timedelta(minutes=10)
        return timezone.now() <= ten_minutes_after and self.status == 'scheduled'

    def is_past_due(self):
        # Check if appointment is more than 10 minutes past its scheduled time
        ten_minutes_after = self.appointment_date + timezone.timedelta(minutes=10)
        return timezone.now() > ten_minutes_after and self.status == 'scheduled'

    def can_be_cancelled(self):
        # Allow cancellation for:
        # 1. Upcoming scheduled appointments (for both doctor and patient)
        # 2. Past scheduled appointments (for doctors only)
        # 3. Completed appointments (for doctors only)
        return (self.is_upcoming() or  # Upcoming appointments
                self.status == 'completed' or  # Completed appointments
                (self.status == 'scheduled' and not self.is_upcoming()))  # Past scheduled appointments

    def can_be_rescheduled(self):
        return (self.is_upcoming() or 
                (self.status == 'scheduled' and self.appointment_date <= timezone.now()))

    def can_be_completed(self):
        return (
            self.status == 'scheduled' and 
            self.appointment_date <= timezone.now() and 
            not self.status in ['completed', 'cancelled']
        )

    @property
    def is_rescheduled(self):
        return self.status == 'rescheduled' or self.original_date is not None

    def reschedule(self, new_date):
        if not self.original_date:  # Only set original date if this is the first reschedule
            self.original_date = self.appointment_date
        self.appointment_date = new_date
        self.status = 'rescheduled'
        self.save()

class DoctorSchedule(models.Model):
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    day_of_week = models.IntegerField(choices=[(i, i) for i in range(7)])  # 0=Monday, 6=Sunday
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['doctor', 'day_of_week']
        
    def __str__(self):
        return f"{self.doctor.get_full_name()} - Day {self.day_of_week}"

class TimeSlot(models.Model):
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_booked = models.BooleanField(default=False)
    appointment = models.OneToOneField(Appointment, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['start_time']
        
    def __str__(self):
        return f"{self.doctor.get_full_name()} - {self.start_time}" 