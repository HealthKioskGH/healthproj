from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    specialization = models.CharField(max_length=100)
    license_number = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    
    def __str__(self):
        return f"Dr. {self.user.get_full_name()}"

    @property
    def assigned_patients(self):
        return self.user.assigned_patients.all()

    @property
    def doctor_appointments(self):
        return self.user.doctor_appointments.all()

    @property
    def monitored_patients(self):
        return self.user.monitored_patients.all()

    @property
    def doctor_alerts(self):
        return self.user.doctor_alerts.all()

class DoctorNote(models.Model):
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='written_notes')
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor_notes')
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']

class PatientMonitoring(models.Model):
    SEVERITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    )
    
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='monitoring_settings')
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='being_monitored_by')
    metric = models.CharField(max_length=100)  # e.g., 'blood_pressure', 'heart_rate'
    min_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['doctor', 'patient', 'metric']

class Alert(models.Model):
    monitoring = models.ForeignKey(PatientMonitoring, on_delete=models.CASCADE)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
