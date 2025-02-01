from rest_framework import serializers
from .models import VitalSigns, MedicalRecord, Symptom, HealthProfile

class VitalSignsSerializer(serializers.ModelSerializer):
    bmi_status = serializers.SerializerMethodField()

    class Meta:
        model = VitalSigns
        fields = ['id', 'height', 'weight', 'blood_pressure', 'temperature', 
                 'pulse_rate', 'bmi', 'bmi_status', 'recorded_at']
        read_only_fields = ['bmi', 'bmi_status']

    def get_bmi_status(self, obj):
        """Return BMI category based on calculated BMI"""
        if obj.bmi is None:
            return "Not available"
        
        bmi = float(obj.bmi)
        if bmi < 18.5:
            return "Underweight"
        elif 18.5 <= bmi < 25:
            return "Normal weight"
        elif 25 <= bmi < 30:
            return "Overweight"
        else:
            return "Obese"

class MedicalRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalRecord
        fields = ['id', 'patient', 'condition', 'diagnosis', 'treatment', 
                 'doctor', 'date_recorded']
        read_only_fields = ['id', 'date_recorded']

class SymptomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Symptom
        fields = ['id', 'patient', 'symptom_name', 'severity', 'description', 
                 'onset_date', 'recorded_at']
        read_only_fields = ['id', 'recorded_at']

class HealthProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthProfile
        fields = ['id', 'patient', 'blood_type', 'allergies', 'chronic_conditions',
                 'medications', 'emergency_contact_name', 'emergency_contact_phone', 
                 'last_updated']
        read_only_fields = ['id', 'last_updated'] 