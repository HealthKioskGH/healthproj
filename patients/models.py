from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse

class VitalSigns(models.Model):
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    height = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0)], default=1.70)  # in meters
    weight = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0)])  # in kg
    blood_pressure = models.CharField(max_length=20)  # Format: "120/80"
    temperature = models.DecimalField(max_digits=4, decimal_places=1)
    pulse_rate = models.IntegerField(validators=[MinValueValidator(0)])
    bmi = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    def calculate_bmi(self):
        """Calculate BMI using weight (kg) and height (m)"""
        try:
            if self.height and self.weight and float(self.height) > 0:
                # Height is in meters, weight in kg
                # BMI formula: weight (kg) / (height (m))²
                height_in_meters = float(self.height)
                weight_in_kg = float(self.weight)
                bmi = weight_in_kg / (height_in_meters ** 2)
                return round(bmi, 2)
        except (ValueError, ZeroDivisionError):
            return None
        return None

    def save(self, *args, **kwargs):
        self.bmi = self.calculate_bmi()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-recorded_at']

class MedicalRecord(models.Model):
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    condition = models.CharField(max_length=200)
    diagnosis = models.TextField()
    treatment = models.TextField()
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='diagnosed_records')
    date_recorded = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date_recorded']

class Symptom(models.Model):
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    symptom_name = models.CharField(max_length=255)
    severity = models.IntegerField(null=True, blank=True)
    description = models.TextField()
    onset_date = models.DateField()
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-recorded_at']

class HealthProfile(models.Model):
    patient = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    blood_type = models.CharField(max_length=5, blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    medical_conditions = models.TextField(blank=True, null=True)  # This stores chronic conditions
    current_medications = models.TextField(blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True, null=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.patient.username}'s Health Profile"

    class Meta:
        verbose_name = "Health Profile"
        verbose_name_plural = "Health Profiles"

class Kiosk(models.Model):
    STATUS_CHOICES = [
        ('Operational', 'Operational'),
        ('Maintenance', 'Maintenance'),
        ('Offline', 'Offline'),
    ]

    name = models.CharField(max_length=200)
    location = models.CharField(max_length=500)
    latitude = models.FloatField()
    longitude = models.FloatField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Operational')
    hours = models.CharField(max_length=200)
    users_today = models.IntegerField(default=0)
    wait_time = models.IntegerField(default=0)  # in minutes
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def directions_url(self):
        return f"https://www.openstreetmap.org/directions?from=&to={self.latitude}%2C{self.longitude}"

    @property
    def booking_url(self):
        return reverse('appointments:book')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'status': self.status,
            'hours': self.hours,
            'users_today': self.users_today,
            'wait_time': self.wait_time,
            'directions_url': self.directions_url,
            'booking_url': self.booking_url,
        }
