from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''

@register.filter
def split(value, delimiter):
    """Split a string value by delimiter"""
    return value.split(delimiter)

@register.filter
def bp_status(blood_pressure):
    """
    Calculate blood pressure status from a blood pressure string (e.g. '120/80')
    Returns: tuple (status_class, status_text)
    """
    try:
        systolic, diastolic = map(int, blood_pressure.split('/'))
        if systolic >= 140 or diastolic >= 90:
            return 'danger'
        elif systolic >= 120 or diastolic >= 80:
            return 'warning'
        else:
            return 'success'
    except (ValueError, AttributeError):
        return 'warning'  # Default case if there's an error 