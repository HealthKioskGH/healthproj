from django.shortcuts import render, redirect

def home_view(request):
    """
    Home page view that redirects to accounts index
    """
    if request.user.is_authenticated:
        if request.user.is_patient():
            return redirect('patients:dashboard')
        elif request.user.is_doctor():
            return redirect('doctors:dashboard')
        elif request.user.is_staff:
            return redirect('admin:index')
    return redirect('accounts:index')
