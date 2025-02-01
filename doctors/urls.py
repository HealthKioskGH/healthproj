from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('notes', views.DoctorNoteViewSet, basename='note')
router.register('monitoring', views.PatientMonitoringViewSet, basename='monitoring')
router.register('alerts', views.AlertViewSet, basename='alert')

app_name = 'doctors'

# Regular URL patterns
urlpatterns = [
    path('dashboard/', views.DoctorDashboardView.as_view(), name='dashboard'),
    path('update-profile/', views.UpdateProfileView.as_view(), name='update_profile'),
]

# API URL patterns
api_urlpatterns = [
    path('', include(router.urls)),
]

# Use different patterns based on whether this is being included as API or regular URLs
def get_patterns(is_api=False):
    return api_urlpatterns if is_api else urlpatterns 