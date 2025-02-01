from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth import get_user_model
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views import View
from appointments.models import Appointment

User = get_user_model()

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff

class AdminDashboardView(AdminRequiredMixin, TemplateView):
    template_name = 'admin/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['doctors'] = User.objects.filter(user_type='doctor')
        context['doctor_count'] = context['doctors'].count()
        context['patient_count'] = User.objects.filter(user_type='patient').count()
        context['appointment_count'] = Appointment.objects.count()
        return context

class CreateDoctorView(AdminRequiredMixin, View):
    def post(self, request):
        # Validate passwords match
        if request.POST['password1'] != request.POST['password2']:
            messages.error(request, 'Passwords do not match')
            return redirect('admin:dashboard')

        try:
            # Create doctor account
            doctor = User.objects.create_user(
                username=request.POST['username'],
                email=request.POST['email'],
                password=request.POST['password1'],
                first_name=request.POST['first_name'],
                last_name=request.POST['last_name'],
                user_type='doctor',
                specialization=request.POST['specialization'],
                license_number=request.POST['license_number'],
                phone_number=request.POST.get('phone_number', '')
            )
            messages.success(request, f'Doctor account created for {doctor.get_full_name()}')
        except Exception as e:
            messages.error(request, f'Error creating doctor account: {str(e)}')

        return redirect('admin:dashboard')

class EditDoctorView(AdminRequiredMixin, View):
    def post(self, request):
        doctor = get_object_or_404(User, id=request.POST['doctor_id'], user_type='doctor')
        try:
            # Update doctor information
            doctor.first_name = request.POST['first_name']
            doctor.last_name = request.POST['last_name']
            doctor.email = request.POST['email']
            doctor.specialization = request.POST['specialization']
            doctor.license_number = request.POST['license_number']
            doctor.phone_number = request.POST.get('phone_number', '')
            
            # Update password if provided
            if request.POST.get('password1'):
                if request.POST['password1'] == request.POST['password2']:
                    doctor.set_password(request.POST['password1'])
                else:
                    messages.error(request, 'Passwords do not match')
                    return redirect('admin:dashboard')
            
            doctor.save()
            messages.success(request, f'Doctor account updated for {doctor.get_full_name()}')
        except Exception as e:
            messages.error(request, f'Error updating doctor account: {str(e)}')

        return redirect('admin:dashboard')

class ToggleDoctorStatusView(AdminRequiredMixin, View):
    def post(self, request, doctor_id):
        doctor = get_object_or_404(User, id=doctor_id, user_type='doctor')
        try:
            doctor.is_active = not doctor.is_active
            doctor.save()
            status = 'activated' if doctor.is_active else 'deactivated'
            messages.success(request, f'Doctor account {status} for {doctor.get_full_name()}')
        except Exception as e:
            messages.error(request, f'Error toggling doctor status: {str(e)}')

        return redirect('admin:dashboard')

class GetDoctorDataView(AdminRequiredMixin, View):
    def get(self, request, doctor_id):
        doctor = get_object_or_404(User, id=doctor_id, user_type='doctor')
        return JsonResponse({
            'first_name': doctor.first_name,
            'last_name': doctor.last_name,
            'email': doctor.email,
            'specialization': doctor.specialization,
            'license_number': doctor.license_number,
            'phone_number': doctor.phone_number
        }) 