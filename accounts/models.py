from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
        ('admin', 'Admin'),
    )
    
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='patient')
    phone_number = models.CharField(max_length=15, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    
    # Additional fields for doctors
    specialization = models.CharField(max_length=100, blank=True)
    license_number = models.CharField(max_length=50, blank=True)
    years_of_experience = models.IntegerField(null=True, blank=True)
    qualifications = models.TextField(blank=True)
    hospital_affiliations = models.TextField(blank=True)
    languages = models.CharField(max_length=200, blank=True)
    working_hours = models.CharField(max_length=100, blank=True)
    emergency_contact = models.CharField(max_length=200, blank=True)
    office_address = models.TextField(blank=True)
    
    # Field to track assigned doctor for patients
    assigned_doctor = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, 
                                      related_name='assigned_patients', limit_choices_to={'user_type': 'doctor'})
    
    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        null=True,
        blank=True
    )
    
    class Meta:
        db_table = 'auth_user'
        
    def is_patient(self):
        return self.user_type == 'patient'
        
    def is_doctor(self):
        return self.user_type == 'doctor'

    @property
    def profile_picture_url(self):
        if self.profile_picture and hasattr(self.profile_picture, 'url'):
            try:
                return self.profile_picture.url
            except:
                pass
        return f"{settings.STATIC_URL}images/default-avatar.png"
