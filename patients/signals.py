from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import HealthProfile

User = get_user_model()

@receiver(post_save, sender=User)
def create_health_profile(sender, instance, created, **kwargs):
    """
    Signal to automatically create a HealthProfile when a new patient user is created
    """
    if created and instance.user_type == 'patient':
        HealthProfile.objects.create(patient=instance)

@receiver(post_save, sender=User)
def save_health_profile(sender, instance, **kwargs):
    """
    Signal to save the HealthProfile when the user is saved
    """
    if instance.user_type == 'patient':
        try:
            instance.healthprofile.save()
        except HealthProfile.DoesNotExist:
            HealthProfile.objects.create(patient=instance) 