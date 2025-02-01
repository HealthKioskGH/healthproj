from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'patients'

# Create API router
router = DefaultRouter()
router.register('vitals', views.VitalSignViewSet, basename='vital')
router.register('records', views.MedicalRecordViewSet, basename='record')
router.register('symptoms', views.SymptomViewSet, basename='symptom')
router.register('profiles', views.HealthProfileViewSet, basename='profile')

urlpatterns = [
    # Regular views
    path('dashboard/', views.PatientDashboardView.as_view(), name='dashboard'),
    path('vitals/', views.VitalSignsView.as_view(), name='vitals'),
    path('symptoms/', views.SymptomsView.as_view(), name='symptoms'),
    path('assign-doctor/', views.AssignDoctorView.as_view(), name='assign_doctor'),
    path('profile/', views.profile_form, name='profile'),
    path('profile/update/', views.profile_form, name='profile-update'),
    path('doctors/', views.DoctorsListView.as_view(), name='doctors'),
    path('calculate-bmi/', views.calculate_bmi, name='calculate_bmi'),
    path('find-store/', views.find_store, name='find-store'),
    path('find-kiosk/', views.find_kiosk, name='find-kiosk'),
    
    # API endpoints
    path('api/', include(router.urls)),
    path('check-email-verification/', views.check_email_verification, name='check_email_verification'),
] 