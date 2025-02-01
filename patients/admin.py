from django.contrib import admin
from .models import VitalSigns, MedicalRecord, Symptom, HealthProfile, Kiosk

@admin.register(VitalSigns)
class VitalSignsAdmin(admin.ModelAdmin):
    list_display = ('patient', 'temperature', 'pulse_rate', 'blood_pressure', 'weight', 'bmi', 'recorded_at')
    list_filter = ('recorded_at', 'patient')
    search_fields = ('patient__username', 'patient__email')
    readonly_fields = ('bmi',)

@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ('patient', 'condition', 'doctor', 'date_recorded')
    list_filter = ('date_recorded', 'doctor')
    search_fields = ('patient__username', 'condition', 'diagnosis')

@admin.register(Symptom)
class SymptomAdmin(admin.ModelAdmin):
    list_display = ('patient', 'symptom_name', 'severity', 'onset_date', 'recorded_at')
    list_filter = ('recorded_at', 'severity')
    search_fields = ('patient__username', 'symptom_name')

@admin.register(HealthProfile)
class HealthProfileAdmin(admin.ModelAdmin):
    list_display = ('get_username', 'blood_type', 'emergency_contact_name')
    search_fields = ('patient__username', 'patient__email', 'blood_type')
    list_filter = ('blood_type',)
    
    def get_username(self, obj):
        return obj.patient.username
    get_username.short_description = 'Patient'
    
    fieldsets = (
        ('Patient Information', {
            'fields': ('user', 'blood_type')
        }),
        ('Medical Information', {
            'fields': ('allergies', 'medical_conditions', 'current_medications')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship')
        }),
    )

@admin.register(Kiosk)
class KioskAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'status', 'users_today', 'wait_time', 'updated_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'location')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'location', 'status')
        }),
        ('Map Location', {
            'fields': ('latitude', 'longitude'),
            'description': 'Enter the exact coordinates for the kiosk location. You can use Google Maps to find coordinates.'
        }),
        ('Operating Details', {
            'fields': ('hours', 'users_today', 'wait_time')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
