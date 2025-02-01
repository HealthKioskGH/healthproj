from rest_framework import serializers
from .models import DoctorNote, PatientMonitoring, Alert

class DoctorNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorNote
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')

class PatientMonitoringSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientMonitoring
        fields = '__all__'
        read_only_fields = ('id', 'created_at')

class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = '__all__'
        read_only_fields = ('id', 'created_at') 