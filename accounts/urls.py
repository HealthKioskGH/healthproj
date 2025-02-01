from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.index_view, name='index'),
    path('register/', views.PatientSignupView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(next_page='accounts:index'), name='logout'),
    path('patient/login/', views.PatientLoginView.as_view(), name='patient_login'),
    path('doctor/login/', views.DoctorLoginView.as_view(), name='doctor_login'),
    path('extend-session/', views.extend_session, name='extend_session'),
    path('check-username/', views.check_username, name='check_username'),
    path('update-profile-picture/', views.update_profile_picture, name='update_profile_picture'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    path('verify-email/', views.VerifyEmailView.as_view(), name='verify_email'),
    path('send-verification/', views.send_verification, name='send_verification'),
]