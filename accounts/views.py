from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib import messages
from .forms import CustomSignupForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth import get_user_model
from allauth.account.views import LoginView, SignupView
from django.urls import reverse, reverse_lazy
from django.core.exceptions import ValidationError
from smtplib import SMTPAuthenticationError, SMTPException
from django.core.mail import send_mail, get_connection
from django.conf import settings
from django.contrib.auth.views import PasswordResetConfirmView
from allauth.account.utils import send_email_confirmation
from allauth.account.models import EmailAddress, EmailConfirmation
from patients.models import HealthProfile
import logging
import socket
import time
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
import traceback
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from datetime import timedelta

logger = logging.getLogger(__name__)

class PatientLoginView(LoginView):
    template_name = 'accounts/patient_login.html'
    
    def form_valid(self, form):
        user = form.user
        if user.is_patient():
            # Check if user has a health profile, create if not exists
            try:
                health_profile = HealthProfile.objects.get(patient=user)
            except HealthProfile.DoesNotExist:
                health_profile = HealthProfile.objects.create(
                    patient=user
                )
            
            # Check if user has a verified email
            email_verified = EmailAddress.objects.filter(
                user=user,
                email=user.email,
                verified=True
            ).exists()
            
            # If user has email but no EmailAddress record, create one
            if not EmailAddress.objects.filter(user=user).exists() and user.email:
                EmailAddress.objects.create(
                    user=user,
                    email=user.email,
                    primary=True,
                    verified=True
                )
            
            # If email is not verified, show warning
            if not email_verified and user.email:
                messages.warning(
                    self.request,
                    'Please verify your email address to ensure account recovery options.'
                )
            
            return super().form_valid(form)
        else:
            form.add_error(None, 'This account is not registered as a patient.')
            return self.form_invalid(form)

class DoctorLoginView(LoginView):
    template_name = 'accounts/doctor_login.html'
    
    def form_valid(self, form):
        user = form.user
        if user.is_doctor():
            login(self.request, user)
            return redirect('doctors:dashboard')
        else:
            form.add_error(None, 'This account is not registered as a doctor.')
            return self.form_invalid(form)

class PatientSignupView(SignupView):
    template_name = 'accounts/register.html'
    form_class = CustomSignupForm
    
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                if field == '__all__':
                    messages.error(self.request, error)
                else:
                    messages.error(self.request, f"{field.title()}: {error}")
        return super().form_invalid(form)
    
    def form_valid(self, form):
        try:
            print("Starting registration process...")
            
            # Save the form data first
            self.user = form.save(self.request)
            print(f"User created: {self.user.username}")
            
            # Set user type
            self.user.user_type = 'patient'
            self.user.save()
            
            # Create health profile only if it doesn't exist
            try:
                health_profile, created = HealthProfile.objects.get_or_create(
                    patient=self.user,
                    defaults={
                        'blood_type': '',
                        'allergies': 'None',
                        'medical_conditions': 'None',
                        'current_medications': 'None',
                        'emergency_contact_name': '',
                        'emergency_contact_phone': '',
                        'emergency_contact_relationship': ''
                    }
                )
                print(f"Health profile {'created' if created else 'retrieved'}: {health_profile}")
            except Exception as profile_error:
                print(f"Health profile error: {str(profile_error)}")
            
            # Create email address record only if email is provided
            if self.user.email:
                try:
                    email_address, created = EmailAddress.objects.get_or_create(
                        user=self.user,
                        email=self.user.email,
                        defaults={
                            'primary': True,
                            'verified': False
                        }
                    )
                    
                    if not email_address.verified:
                        # Create email confirmation
                        confirmation = EmailConfirmation.create(email_address)
                        confirmation.sent = timezone.now()
                        confirmation.save()
                        
                        # Send the confirmation email
                        confirmation.send(self.request, signup=True)
                        print("Verification email sent successfully")
                    
                except Exception as e:
                    print(f"Email setup error: {str(e)}")
                    messages.warning(
                        self.request,
                        'Account created, but there was an issue sending the verification email. '
                        'You can request a new verification email from your profile.'
                    )
            
            # Log the user in
            auth_user = authenticate(
                self.request,
                username=self.user.username,
                password=form.cleaned_data.get('password1')
            )
            if auth_user:
                login(self.request, auth_user)
            
            if self.user.email:
                messages.success(
                    self.request,
                    'Account created successfully! Please check your email to verify your account.'
                )
                # Store email in session
                self.request.session['verification_email'] = self.user.email
                # Redirect to verify email page
                return redirect('accounts:verify_email')
            else:
                messages.success(
                    self.request,
                    'Account created successfully! You can add an email later for verification.'
                )
                return redirect('patients:dashboard')
            
        except Exception as e:
            print(f"Registration error: {str(e)}")
            print(traceback.format_exc())
            messages.error(
                self.request,
                'An error occurred during registration. Please try again.'
            )
            if hasattr(self, 'user') and self.user:
                self.user.delete()
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

def index_view(request):
    return render(request, 'accounts/index.html')

@login_required
@require_POST
def extend_session(request):
    """Update the user's last activity timestamp"""
    if not request.is_ajax():
        return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
        
    request.session['last_activity'] = timezone.now().isoformat()
    return JsonResponse({
        'status': 'success',
        'message': 'Session extended successfully'
    })

def check_username(request):
    """Check if a username is available."""
    username = request.GET.get('username', '').strip()
    
    if len(username) < 3:
        return JsonResponse({'available': False, 'message': 'Username must be at least 3 characters long'})
    
    User = get_user_model()
    exists = User.objects.filter(username__iexact=username).exists()
    
    return JsonResponse({
        'available': not exists,
        'message': 'Username is available' if not exists else 'Username is already taken'
    })

@login_required
@require_POST
def update_profile_picture(request):
    try:
        if 'profile_picture' in request.FILES:
            file = request.FILES['profile_picture']
            
            if request.user.profile_picture:
                request.user.profile_picture.delete(save=False)
            
            request.user.profile_picture = file
            request.user.save()
            request.user.refresh_from_db()
            
            return JsonResponse({
                'success': True,
                'message': 'Profile picture updated successfully',
                'url': request.user.profile_picture_url
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    
    return JsonResponse({
        'success': False,
        'error': 'No file was uploaded'
    }, status=400)

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'patients/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:patient_login')
    
    def form_valid(self, form):
        user = form.save()
        # Update session to prevent user from being logged out
        update_session_auth_hash(self.request, user)
        
        messages.success(
            self.request,
            'Your password has been successfully changed. Please login with your new password.'
        )
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(
            self.request,
            'There was an error changing your password. Please make sure your passwords match and meet the requirements.'
        )
        return super().form_invalid(form)

@login_required
def resend_verification(request):
    try:
        email_address = EmailAddress.objects.get(user=request.user, email=request.user.email)
        
        if not email_address.verified:
            # Generate new verification
            confirmation = send_email_confirmation(request, request.user)
            verify_url = request.build_absolute_uri(
                reverse('account_confirm_email', args=[confirmation.key])
            )
            
            # Create email content
            context = {
                'user': request.user,
                'verify_url': verify_url,
            }
            html_message = render_to_string('patients/email_verification.html', context)
            plain_message = strip_tags(html_message)
            
            # Send verification email
            send_mail(
                subject='Verify Your Email Address',
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[request.user.email],
                html_message=html_message,
                fail_silently=False,
            )
            messages.success(request, 'Verification email has been sent! Please check your inbox.')
        else:
            messages.info(request, 'This email is already verified.')
            
    except EmailAddress.DoesNotExist:
        # Create new unverified email address
        if request.user.email:
            email_address = EmailAddress.objects.create(
                user=request.user,
                email=request.user.email,
                primary=True,
                verified=False
            )
            # Send verification email
            confirmation = send_email_confirmation(request, request.user)
            messages.success(request, 'Verification email has been sent! Please check your inbox.')
    except Exception as e:
        messages.error(request, f'Error sending verification email: {str(e)}')
    
    return redirect('patients:profile')

class VerifyEmailView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/verify_email.html'
    login_url = 'accounts:patient_login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['email'] = self.request.user.email
        return context

@login_required
def send_verification(request):
    try:
        send_email_confirmation(request, request.user)
        messages.success(request, 'Verification email has been sent! Please check your inbox.')
    except Exception as e:
        messages.error(request, 'There was an error sending the verification email. Please try again.')
    
    return redirect('accounts:verify_email')
