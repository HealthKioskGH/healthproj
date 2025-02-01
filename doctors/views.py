from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import DoctorNote, PatientMonitoring, Alert
from .serializers import DoctorNoteSerializer, PatientMonitoringSerializer, AlertSerializer
from appointments.models import Appointment
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View, TemplateView
from django.utils import timezone
from django.http import JsonResponse
from decimal import Decimal
import json
from patients.models import VitalSigns
from django.conf import settings

User = get_user_model()

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

class DoctorDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'doctors/dashboard.html'
    
    def test_func(self):
        return self.request.user.is_doctor()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['DEFAULT_PROFILE_URL'] = settings.DEFAULT_PROFILE_URL
        context['STATIC_URL'] = settings.STATIC_URL
        user = self.request.user
        today = timezone.now().date()
        
        # Get assigned patients with their health profiles
        assigned_patients = User.objects.filter(
            assigned_doctor=user
        ).select_related('healthprofile')
        
        # Get recent appointments
        recent_appointments = Appointment.objects.filter(
            doctor=user
        ).select_related('patient', 'patient__healthprofile').order_by('-appointment_date')[:5]
        
        # Get vitals data for each patient using the new VitalSigns model
        vitals_data = {}
        for patient in assigned_patients:
            vitals = VitalSigns.objects.filter(patient=patient).order_by('-recorded_at')[:10]
            if vitals:
                vitals_data[str(patient.id)] = [{
                    'date': vital.recorded_at.strftime('%b %d'),
                    'pulse_rate': float(vital.pulse_rate) if vital.pulse_rate else None,
                    'blood_pressure': vital.blood_pressure,
                    'temperature': float(vital.temperature) if vital.temperature else None,
                    'bmi': float(vital.bmi) if vital.bmi else None
                } for vital in vitals]
        context['vitals_data'] = json.dumps(vitals_data, cls=DecimalEncoder)
        
        # Get today's appointments
        context['today_appointments'] = Appointment.objects.filter(
            doctor=user,
            appointment_date__date=today,
            status='scheduled'
        ).order_by('appointment_date')
        
        # Get all upcoming appointments
        context['upcoming_appointments'] = Appointment.objects.filter(
            doctor=user,
            appointment_date__gte=timezone.now(),
            status='scheduled'
        ).order_by('appointment_date')[:10]
        
        # Get recent alerts
        context['recent_alerts'] = Alert.objects.filter(
            monitoring__doctor=user,
            is_read=False
        ).order_by('-created_at')[:5]
        
        # Get monitored patients
        context['monitored_patients'] = PatientMonitoring.objects.filter(
            doctor=user,
            is_active=True
        ).select_related('patient')
        
        # Get recent vitals
        context['recent_vitals'] = VitalSigns.objects.filter(
            patient__assigned_doctor=user
        ).order_by('-recorded_at')[:5]
        
        # Add to context
        context.update({
            'assigned_patients': assigned_patients,
            'recent_appointments': recent_appointments,
            'page': 'dashboard'
        })
        
        return context

class DoctorNoteViewSet(viewsets.ModelViewSet):
    serializer_class = DoctorNoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_doctor():
            return DoctorNote.objects.filter(doctor=self.request.user)
        return DoctorNote.objects.filter(patient=self.request.user)

    def perform_create(self, serializer):
        serializer.save(doctor=self.request.user)

class PatientMonitoringViewSet(viewsets.ModelViewSet):
    serializer_class = PatientMonitoringSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_doctor():
            return PatientMonitoring.objects.filter(doctor=self.request.user)
        return PatientMonitoring.objects.filter(patient=self.request.user)

    def perform_create(self, serializer):
        serializer.save(doctor=self.request.user)

class AlertViewSet(viewsets.ModelViewSet):
    serializer_class = AlertSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_doctor():
            return Alert.objects.filter(monitoring__doctor=self.request.user)
        return Alert.objects.filter(monitoring__patient=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        alert = self.get_object()
        alert.is_read = True
        alert.save()
        return Response({'status': 'alert marked as read'})

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'doctors/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        context['today'] = today
        context['assigned_patients'] = self.request.user.assigned_patients.all()
        context['today_appointments'] = self.request.user.doctor_appointments.filter(
            appointment_date__date=today,
            status='scheduled'
        ).order_by('appointment_date')
        context['recent_alerts'] = self.request.user.doctor_alerts.all()[:5]
        context['monitored_patients'] = self.request.user.monitored_patients.all()
        return context

class UpdateProfileView(LoginRequiredMixin, View):
    def post(self, request):
        if not request.user.is_doctor:
            return JsonResponse({
                'success': False,
                'message': 'Only doctors can update their profile.'
            }, status=403)
        
        try:
            # Get form data
            full_name = request.POST.get('full_name', '').strip()
            email = request.POST.get('email', '').strip()
            specialization = request.POST.get('specialization', '').strip()
            license_number = request.POST.get('license_number', '').strip()
            phone_number = request.POST.get('phone_number', '').strip()
            years_of_experience = request.POST.get('years_of_experience', '')
            qualifications = request.POST.get('qualifications', '')
            hospital_affiliations = request.POST.get('hospital_affiliations', '')
            languages = request.POST.get('languages', '')
            working_hours = request.POST.get('working_hours', '')
            emergency_contact = request.POST.get('emergency_contact', '')
            office_address = request.POST.get('office_address', '')

            # Validate required fields
            if not all([full_name, email, specialization, license_number]):
                return JsonResponse({
                    'success': False,
                    'message': 'Please fill in all required fields.'
                }, status=400)

            # Split full name into first and last name
            name_parts = full_name.split(' ', 1)
            request.user.first_name = name_parts[0]
            request.user.last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            # Update user fields
            request.user.email = email
            request.user.specialization = specialization
            request.user.license_number = license_number
            request.user.phone_number = phone_number
            request.user.years_of_experience = years_of_experience
            request.user.qualifications = qualifications
            request.user.hospital_affiliations = hospital_affiliations
            request.user.languages = languages
            request.user.working_hours = working_hours
            request.user.emergency_contact = emergency_contact
            request.user.office_address = office_address
            request.user.save()

            return JsonResponse({
                'success': True,
                'message': 'Profile updated successfully',
                'full_name': request.user.get_full_name(),
                'email': email,
                'specialization': specialization,
                'license_number': license_number,
                'years_of_experience': years_of_experience,
                'qualifications': qualifications,
                'hospital_affiliations': hospital_affiliations,
                'languages': languages,
                'working_hours': working_hours,
                'phone_number': phone_number,
                'emergency_contact': emergency_contact,
                'office_address': office_address
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error updating profile: {str(e)}'
            }, status=500)
