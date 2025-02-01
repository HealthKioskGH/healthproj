from .models import Notification
from patients.models import VitalSigns

def create_notification(recipient, sender, notification_type, title, message, link=''):
    """
    Create a new notification
    """
    return Notification.objects.create(
        recipient=recipient,
        sender=sender,
        notification_type=notification_type,
        title=title,
        message=message,
        link=link
    )

def notify_appointment_created(appointment):
    """
    Create notifications for a new appointment
    """
    # Notify doctor
    create_notification(
        recipient=appointment.doctor,
        sender=appointment.patient,
        notification_type='appointment_created',
        title='New Appointment Request',
        message=f'New appointment request from {appointment.patient.get_full_name()} on {appointment.appointment_date.strftime("%B %d, %Y")} at {appointment.appointment_date.strftime("%I:%M %p")}',
        link=f'/appointments/{appointment.id}/'
    )

def notify_appointment_updated(appointment):
    """
    Create notifications for an updated appointment
    """
    # Notify the other party
    recipient = appointment.doctor if appointment.last_modified_by == appointment.patient else appointment.patient
    create_notification(
        recipient=recipient,
        sender=appointment.last_modified_by,
        notification_type='appointment_updated',
        title='Appointment Updated',
        message=f'Appointment on {appointment.appointment_date.strftime("%B %d, %Y")} at {appointment.appointment_date.strftime("%I:%M %p")} has been updated',
        link=f'/appointments/{appointment.id}/'
    )

def notify_appointment_cancelled(appointment, cancelled_by):
    """
    Create notifications for a cancelled appointment
    """
    # Notify the other party
    recipient = appointment.doctor if cancelled_by == appointment.patient else appointment.patient
    create_notification(
        recipient=recipient,
        sender=cancelled_by,
        notification_type='appointment_cancelled',
        title='Appointment Cancelled',
        message=f'Appointment on {appointment.appointment_date.strftime("%B %d, %Y")} at {appointment.appointment_date.strftime("%I:%M %p")} has been cancelled by {cancelled_by.get_full_name()}',
        link=f'/appointments/{appointment.id}/'
    )

def notify_vital_signs_updated(vital_signs):
    """
    Create notifications for updated vital signs
    """
    if vital_signs.patient.assigned_doctor:
        Notification.objects.create(
            recipient=vital_signs.patient.assigned_doctor,
            sender=vital_signs.patient,
            notification_type='vital_signs_updated',
            title='Vital Signs Updated',
            message=f'Patient {vital_signs.patient.get_full_name()} has updated their vital signs.',
            link=f'/patients/{vital_signs.patient.id}/vitals/'
        )

def notify_symptom_reported(symptom):
    """
    Create notifications for new symptom reports
    """
    if symptom.patient.assigned_doctor:
        create_notification(
            recipient=symptom.patient.assigned_doctor,
            sender=symptom.patient,
            notification_type='symptom_reported',
            title='New Symptom Reported',
            message=f'{symptom.patient.get_full_name()} has reported new symptoms: {symptom.symptom_name}',
            link=f'/patients/{symptom.patient.id}/symptoms/'
        )

def notify_prescription_added(prescription):
    """
    Create notifications for new prescriptions
    """
    create_notification(
        recipient=prescription.patient,
        sender=prescription.doctor,
        notification_type='prescription_added',
        title='New Prescription Added',
        message=f'Dr. {prescription.doctor.get_full_name()} has added a new prescription',
        link=f'/prescriptions/{prescription.id}/'
    )

def notify_test_results(test_result):
    """
    Create notifications for new test results
    """
    create_notification(
        recipient=test_result.patient,
        sender=test_result.doctor,
        notification_type='test_results',
        title='Test Results Available',
        message=f'Your test results for {test_result.test_name} are now available',
        link=f'/test-results/{test_result.id}/'
    )

def notify_primary_doctor_selected(doctor, patient):
    """
    Create a notification when a doctor is selected as primary doctor
    """
    Notification.objects.create(
        recipient=doctor,
        sender=patient,
        notification_type='primary_doctor_selected',
        title='New Primary Patient',
        message=f'{patient.get_full_name()} has selected you as their primary doctor.',
        link=f'/patients/profile/{patient.id}/'  # Link to patient's profile
    ) 