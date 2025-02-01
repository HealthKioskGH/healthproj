from django.contrib import admin
from .models import DoctorNote, PatientMonitoring, Alert

@admin.register(DoctorNote)
class DoctorNoteAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'patient', 'created_at', 'updated_at')
    list_filter = ('doctor', 'patient', 'created_at')
    search_fields = ('doctor__username', 'patient__username', 'note')

@admin.register(PatientMonitoring)
class PatientMonitoringAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'patient', 'metric', 'severity', 'is_active')
    list_filter = ('doctor', 'patient', 'metric', 'severity', 'is_active')
    search_fields = ('doctor__username', 'patient__username', 'metric')

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('monitoring', 'value', 'is_read', 'created_at')
    list_filter = ('monitoring__doctor', 'monitoring__patient', 'is_read', 'created_at')
    search_fields = ('monitoring__doctor__username', 'monitoring__patient__username', 'message')
