from django.urls import path
from . import views

app_name = 'system_admin'

urlpatterns = [
    path('dashboard/', views.AdminDashboardView.as_view(), name='dashboard'),
    path('doctor/create/', views.CreateDoctorView.as_view(), name='create_doctor'),
    path('doctor/edit/', views.EditDoctorView.as_view(), name='edit_doctor'),
    path('doctor/<int:doctor_id>/toggle/', views.ToggleDoctorStatusView.as_view(), name='toggle_doctor_status'),
    path('doctor/<int:doctor_id>/', views.GetDoctorDataView.as_view(), name='get_doctor_data'),
] 