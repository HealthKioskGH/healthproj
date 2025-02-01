from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.views.generic import TemplateView, FormView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils import timezone
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth import get_user_model
from .models import VitalSigns, MedicalRecord, Symptom, HealthProfile, Kiosk
from .serializers import (VitalSignsSerializer, MedicalRecordSerializer,
                         SymptomSerializer, HealthProfileSerializer)
from appointments.models import Appointment
from notifications.utils import (
    notify_vital_signs_updated,
    notify_symptom_reported,
    notify_primary_doctor_selected
)
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics
from rest_framework import status
from django.conf import settings
from django.db.models import Q
import json
from math import radians, sin, cos, sqrt, atan2
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail, BadHeaderError
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.core.exceptions import ValidationError
import logging
import time
from allauth.account.utils import send_email_confirmation
from django.contrib.auth.decorators import login_required
from allauth.account.models import EmailAddress

User = get_user_model()

logger = logging.getLogger(__name__)

class PatientDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'patients/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        try:
            # Use patient instead of user
            health_profile = HealthProfile.objects.get(patient=user)
        except HealthProfile.DoesNotExist:
            health_profile = HealthProfile.objects.create(patient=user)
            
        # Get upcoming appointments
        upcoming_appointments = Appointment.objects.filter(
            patient=user,
            appointment_date__gte=timezone.now()
        ).order_by('appointment_date')[:5]
        
        # Get past appointments
        past_appointments = Appointment.objects.filter(
            patient=user,
            appointment_date__lt=timezone.now()
        ).order_by('-appointment_date')[:5]
        
        # Get vital signs data
        vital_signs = VitalSigns.objects.filter(patient=user).order_by('recorded_at')
        
        # Prepare data for charts
        dates = []
        bmis = []
        systolic_bp = []
        diastolic_bp = []
        temperatures = []
        pulse_rates = []
        
        for vital in vital_signs:
            date_str = vital.recorded_at.strftime('%Y-%m-%d')
            dates.append(date_str)
            bmis.append(float(vital.bmi) if vital.bmi else None)
            
            # Split blood pressure into systolic and diastolic
            try:
                sys, dia = vital.blood_pressure.split('/')
                systolic_bp.append(int(sys))
                diastolic_bp.append(int(dia))
            except (ValueError, AttributeError):
                systolic_bp.append(None)
                diastolic_bp.append(None)
            
            temperatures.append(float(vital.temperature))
            pulse_rates.append(vital.pulse_rate)
        
        # Add to context
        context['dates'] = json.dumps(dates)
        context['bmis'] = json.dumps(bmis)
        context['systolic_bp'] = json.dumps(systolic_bp)
        context['diastolic_bp'] = json.dumps(diastolic_bp)
        context['temperatures'] = json.dumps(temperatures)
        context['pulse_rates'] = json.dumps(pulse_rates)
        
        # Get recent symptoms
        recent_symptoms = Symptom.objects.filter(
            patient=user
        ).order_by('-recorded_at')[:5]  # Get last 5 symptoms
        
        context.update({
            'health_profile': health_profile,
            'upcoming_appointments': upcoming_appointments,
            'past_appointments': past_appointments,
            'recent_symptoms': recent_symptoms,  # Add recent symptoms to context
            'page': 'dashboard'
        })
        
        return context

class HealthProfileUpdateView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'patients/profile_form.html'
    blood_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']

    def test_func(self):
        return self.request.user.is_patient()

    def get(self, request, *args, **kwargs):
        try:
            health_profile = HealthProfile.objects.get(patient=request.user)
        except HealthProfile.DoesNotExist:
            health_profile = HealthProfile.objects.create(patient=request.user)
        
        context = {
            'health_profile': health_profile,
            'blood_types': self.blood_types
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        health_profile = get_object_or_404(HealthProfile, patient=request.user)
        
        # Update health profile fields
        health_profile.blood_type = request.POST.get('blood_type')
        health_profile.allergies = request.POST.get('allergies')
        health_profile.chronic_conditions = request.POST.get('chronic_conditions')
        health_profile.medications = request.POST.get('medications')
        health_profile.emergency_contact_name = request.POST.get('emergency_contact_name')
        health_profile.emergency_contact_phone = request.POST.get('emergency_contact_phone')
        health_profile.save()

        # Create notification for the assigned doctor
        if request.user.assigned_doctor:
            from notifications.models import Notification
            Notification.objects.create(
                recipient=request.user.assigned_doctor,
                sender=request.user,
                notification_type='health_profile_updated',
                title='Health Profile Updated',
                message=f'Patient {request.user.get_full_name()} has updated their health profile.\n'
                       f'Updated fields include: Blood Type, Allergies, Conditions, Medications, and Emergency Contact.',
                link=f'/patients/{request.user.id}/profile/'
            )
        
        messages.success(request, 'Health profile updated successfully.')
        return redirect('patients:dashboard')

class AssignDoctorView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_patient()
    
    def post(self, request, *args, **kwargs):
        doctor_id = request.POST.get('doctor_id')
        try:
            doctor = User.objects.get(id=doctor_id, user_type='doctor')
            
            # Check if this is a new doctor assignment or a change
            old_doctor = request.user.assigned_doctor
            
            # Assign the new doctor
            request.user.assigned_doctor = doctor
            request.user.save()
            
            # Send notification to the newly assigned doctor
            notify_primary_doctor_selected(doctor, request.user)
            
            messages.success(request, f'Successfully assigned Dr. {doctor.get_full_name()} as your primary doctor.')
            
        except User.DoesNotExist:
            messages.error(request, 'Selected doctor not found.')
        except Exception as e:
            messages.error(request, 'Error assigning doctor. Please try again.')
        
        return redirect('patients:dashboard')

class VitalSignsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'patients/vitals.html'
    
    def test_func(self):
        return self.request.user.is_patient()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vitals_history'] = VitalSigns.objects.filter(
            patient=self.request.user
        ).order_by('-recorded_at')
        return context
    
    def post(self, request, *args, **kwargs):
        try:
            # Convert height from cm to meters, and other values to appropriate types
            height_in_cm = float(request.POST.get('height', 0))
            height_in_meters = height_in_cm / 100  # Convert cm to meters
            weight = float(request.POST.get('weight', 0))
            temperature = float(request.POST.get('temperature', 0))
            pulse_rate = int(request.POST.get('pulse_rate', 0))
            blood_pressure = request.POST.get('blood_pressure', '')

            # Validate the data
            if height_in_cm <= 0 or weight <= 0 or temperature <= 0 or pulse_rate <= 0:
                raise ValueError("All measurements must be greater than zero")

            # Validate height is in reasonable range (50cm to 300cm)
            if height_in_cm < 50 or height_in_cm > 300:
                raise ValueError("Height must be between 50cm and 300cm")

            # Create the vital signs record
            vital_signs = VitalSigns.objects.create(
                patient=request.user,
                height=height_in_meters,  # Save height in meters
                weight=weight,  # In kg
                temperature=temperature,
                pulse_rate=pulse_rate,
                blood_pressure=blood_pressure
            )
            
            # Create notification for the assigned doctor
            if hasattr(request.user, 'assigned_doctor') and request.user.assigned_doctor:
                notify_vital_signs_updated(vital_signs)
            
            messages.success(request, 'Vital signs recorded successfully.')
            
        except ValueError as e:
            messages.error(request, f'Invalid input: {str(e)}')
        except Exception as e:
            messages.error(request, f'Error recording vital signs: {str(e)}')
        
        return redirect('patients:vitals')

class SymptomsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'patients/symptoms.html'
    
    def test_func(self):
        return self.request.user.is_patient()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['symptoms_history'] = Symptom.objects.filter(
            patient=self.request.user
        ).order_by('-recorded_at')
        context['today'] = timezone.now().date()
        return context
    
    def post(self, request, *args, **kwargs):
        try:
            has_pain = request.POST.get('has_pain') == 'yes'
            
            # Create base symptom
            symptom = Symptom.objects.create(
                patient=request.user,
                symptom_name=request.POST.get('symptom_name'),
                description=request.POST.get('description'),
                onset_date=request.POST.get('onset_date')
            )
            
            if has_pain:
                # Handle multiple pain locations
                pain_locations = request.POST.getlist('pain_location[]')
                pain_types = request.POST.getlist('pain_type[]')
                severities = request.POST.getlist('severity[]')
                
                # Use the highest severity from all pain locations
                max_severity = max(int(s) for s in severities if s) if severities else None
                if max_severity:
                    symptom.severity = max_severity
                
                # Combine pain information into description
                pain_descriptions = []
                for i in range(len(pain_locations)):
                    if i < len(pain_locations) and i < len(pain_types) and i < len(severities):
                        pain_desc = f"Pain in {pain_locations[i]}: {pain_types[i]} type, severity {severities[i]}/10"
                        pain_descriptions.append(pain_desc)
                
                if pain_descriptions:
                    symptom.description = f"{symptom.description}\n\nPain Details:\n" + "\n".join(pain_descriptions)
            
            symptom.save()
            
            # Create notification for the assigned doctor
            notify_symptom_reported(symptom)
            
            messages.success(request, 'Symptom logged successfully.')
            
        except Exception as e:
            messages.error(request, f'Error logging symptom: {str(e)}')
        
        return redirect('patients:symptoms')

class VitalSignViewSet(viewsets.ModelViewSet):
    serializer_class = VitalSignsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_doctor():
            return VitalSigns.objects.all()
        return VitalSigns.objects.filter(patient=self.request.user)

    def perform_create(self, serializer):
        serializer.save(patient=self.request.user)

class MedicalRecordViewSet(viewsets.ModelViewSet):
    serializer_class = MedicalRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_doctor():
            return MedicalRecord.objects.all()
        return MedicalRecord.objects.filter(patient=self.request.user)

class SymptomViewSet(viewsets.ModelViewSet):
    serializer_class = SymptomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_doctor():
            return Symptom.objects.all()
        return Symptom.objects.filter(patient=self.request.user)

    def perform_create(self, serializer):
        serializer.save(patient=self.request.user)

class HealthProfileViewSet(viewsets.ModelViewSet):
    serializer_class = HealthProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_doctor():
            return HealthProfile.objects.all()
        return HealthProfile.objects.filter(patient=self.request.user)

    def perform_create(self, serializer):
        serializer.save(patient=self.request.user)

class DoctorsListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'patients/doctors.html'
    
    def test_func(self):
        return self.request.user.is_patient()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['DEFAULT_PROFILE_URL'] = settings.DEFAULT_PROFILE_URL
        context['STATIC_URL'] = settings.STATIC_URL
        # Get all doctors
        context['available_doctors'] = User.objects.filter(
            user_type='doctor',
            is_active=True
        ).order_by('first_name', 'last_name')
        return context

@csrf_exempt
def calculate_bmi(request):
    try:
        if request.method == 'POST':
            height = float(request.POST.get('height', 0))
            weight = float(request.POST.get('weight', 0))
            height_unit = request.POST.get('height_unit')
            weight_unit = request.POST.get('weight_unit')

            print(f"Received data: height={height}, weight={weight}, height_unit={height_unit}, weight_unit={weight_unit}")  # Debug print

            # Convert height to meters
            if height_unit == 'ft':
                height = height * 30.48  # Convert feet to cm
            height = height / 100  # Convert cm to meters

            # Convert weight to kg
            if weight_unit == 'lbs':
                weight = weight * 0.453592  # Convert lbs to kg

            # Calculate BMI
            bmi = weight / (height * height)
            
            print(f"Calculated BMI: {bmi}")  # Debug print
            
            # Determine category and message
            if bmi < 18.5:
                category = 'Underweight'
                message = 'You may need to gain some weight. Consult with your doctor about a healthy diet plan.'
                color = '#ffc107'
                bg_color = '#fff8e1'
            elif bmi < 25:
                category = 'Normal'
                message = 'You have a healthy weight. Keep maintaining a balanced diet and regular exercise.'
                color = '#4caf50'
                bg_color = '#e8f5e9'
            elif bmi < 30:
                category = 'Overweight'
                message = 'Consider adopting a healthier lifestyle with regular exercise and a balanced diet.'
                color = '#ff9800'
                bg_color = '#fff3e0'
            else:
                category = 'Obese'
                message = 'It\'s recommended to consult with your doctor about weight management strategies.'
                color = '#f44336'
                bg_color = '#ffebee'

            response_data = {
                'bmi': round(bmi, 1),
                'category': category,
                'message': message,
                'color': color,
                'bg_color': bg_color
            }
            print(f"Sending response: {response_data}")  # Debug print
            return JsonResponse(response_data)

    except Exception as e:
        print(f"Error calculating BMI: {str(e)}")  # Debug print
        return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

class VitalSignsCreateView(generics.CreateAPIView):
    serializer_class = VitalSignsSerializer

    def perform_create(self, serializer):
        # Associate the vital signs with the current patient
        patient = self.request.user.patient
        vital_signs = serializer.save(patient=patient)
        return vital_signs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            vital_signs = self.perform_create(serializer)
            # Re-serialize to include calculated BMI
            response_serializer = self.get_serializer(vital_signs)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def find_store(request):
    # Example store data - replace with actual database query or API call
    stores = [
        {
            'name': 'HealthCare Pharmacy',
            'image_url': '/static/images/stores/store1.jpg',
            'is_open': True,
            'rating': 4,
            'review_count': 128,
            'address': '123 Main St, City, State',
            'hours': 'Mon-Sat: 8:00 AM - 10:00 PM, Sun: 9:00 AM - 8:00 PM',
            'phone': '+1 234-567-8900',
            'email': 'contact@healthcarepharmacy.com',
            'services': ['Prescription Services', '24/7 Service', 'Home Delivery'],
            'directions_url': 'https://maps.google.com',
            'website': 'https://healthcarepharmacy.com'
        },
        {
            'name': 'MediCare Plus',
            'image_url': '/static/images/stores/store2.jpg',
            'is_open': True,
            'rating': 5,
            'review_count': 256,
            'address': '456 Oak Ave, City, State',
            'hours': 'Mon-Sun: 24 Hours',
            'phone': '+1 234-567-8901',
            'email': 'info@medicareplus.com',
            'services': ['Prescription Services', '24/7 Service', 'Drive-thru'],
            'directions_url': 'https://maps.google.com',
            'website': 'https://medicareplus.com'
        },
        {
            'name': 'City Pharmacy',
            'image_url': '/static/images/stores/store3.jpg',
            'is_open': False,
            'rating': 4,
            'review_count': 89,
            'address': '789 Pine St, City, State',
            'hours': 'Mon-Fri: 9:00 AM - 7:00 PM, Sat: 10:00 AM - 5:00 PM',
            'phone': '+1 234-567-8902',
            'email': 'support@citypharmacy.com',
            'services': ['Prescription Services', 'Home Delivery', 'Vaccinations'],
            'directions_url': 'https://maps.google.com',
            'website': 'https://citypharmacy.com'
        }
    ]

    # Filter based on search parameters
    query = request.GET.get('q', '').lower()
    service = request.GET.get('service', '')
    distance = request.GET.get('distance', '')

    if query:
        stores = [
            store for store in stores 
            if query in store['name'].lower() or query in store['address'].lower()
        ]

    if service:
        stores = [
            store for store in stores 
            if service.title() in store['services']
        ]

    return render(request, 'patients/find_store.html', {
        'stores': stores,
    })

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two points on Earth using the Haversine formula
    Returns distance in kilometers
    """
    R = 6371  # Earth's radius in kilometers

    lat1, lon1, lat2, lon2 = map(radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c
    
    return distance

def find_kiosk(request):
    query = request.GET.get('q', '')
    distance = request.GET.get('distance', 10)  # Default 10km radius
    service = request.GET.get('service', '')
    user_lat = request.GET.get('lat')
    user_lng = request.GET.get('lng')
    
    # Base queryset
    kiosks = Kiosk.objects.all()
    
    # Filter by search query
    if query:
        kiosks = kiosks.filter(
            Q(name__icontains=query) |
            Q(location__icontains=query)
        )
    
    # Filter by service
    if service:
        kiosks = kiosks.filter(services__contains=[service])
    
    # Filter by distance if user location is provided
    if user_lat and user_lng:
        try:
            max_distance = float(distance)
            filtered_kiosks = []
            
            for kiosk in kiosks:
                dist = calculate_distance(
                    user_lat, user_lng,
                    kiosk.latitude, kiosk.longitude
                )
                if dist <= max_distance:
                    # Add distance to kiosk object for sorting
                    kiosk.distance = round(dist, 2)
                    filtered_kiosks.append(kiosk)
            
            # Sort by distance
            kiosks = sorted(filtered_kiosks, key=lambda x: x.distance)
        except (ValueError, TypeError):
            # If coordinates are invalid, fall back to default ordering
            kiosks = kiosks.order_by('name')
    else:
        kiosks = kiosks.order_by('name')
    
    # Convert kiosks to JSON for map
    kiosks_json = json.dumps([kiosk.to_dict() for kiosk in kiosks])
    
    context = {
        'kiosks': kiosks,
        'kiosks_json': kiosks_json,
        'query': query,
        'distance': distance,
        'service': service,
    }
    
    return render(request, 'patients/find_kiosk.html', context)

def register(request):
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                user.is_active = False
                user.save()
                
                messages.success(request, 'Registration successful! Please check your email to verify your account.')
                return redirect('email_verification')
                
            except Exception as e:
                logger.error(f"Error during registration: {str(e)}")
                messages.error(request, 'An error occurred during registration. Please try again.')
                user.delete()  # Clean up the partially created user
    else:
        form = PatientRegistrationForm()
        
    return render(request, 'patients/register.html', {'form': form})

@login_required
def profile_form(request):
    try:
        health_profile = HealthProfile.objects.get(patient=request.user)
    except HealthProfile.DoesNotExist:
        health_profile = HealthProfile.objects.create(patient=request.user)
    
    if request.method == 'POST':
        try:
            # Update health profile fields
            health_profile.blood_type = request.POST.get('blood_type')
            health_profile.allergies = request.POST.get('allergies')
            health_profile.medical_conditions = request.POST.get('chronic_conditions')  # Match the form field name
            health_profile.current_medications = request.POST.get('medications')  # Match the form field name
            health_profile.emergency_contact_name = request.POST.get('emergency_contact_name')
            health_profile.emergency_contact_phone = request.POST.get('emergency_contact_phone')
            health_profile.save()
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('patients:profile')
            
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
    
    # Get email verification status
    try:
        email_address = EmailAddress.objects.get(
            user=request.user,
            email=request.user.email,
            primary=True
        )
        email_verified = email_address.verified
    except EmailAddress.DoesNotExist:
        email_verified = False
    
    return render(request, 'patients/profile_form.html', {
        'health_profile': health_profile,
        'email_verified': email_verified,
        'page': 'profile_form'
    })

@login_required
def check_email_verification(request):
    try:
        email_address = EmailAddress.objects.get(
            user=request.user,
            email=request.user.email,
            primary=True
        )
        is_verified = email_address.verified
    except EmailAddress.DoesNotExist:
        if request.user.email:
            email_address = EmailAddress.objects.create(
                user=request.user,
                email=request.user.email,
                primary=True,
                verified=True
            )
            is_verified = True
        else:
            is_verified = False
    
    return JsonResponse({'verified': is_verified})
