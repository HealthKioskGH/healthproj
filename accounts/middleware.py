from django.conf import settings
from django.contrib.auth import logout
from django.utils import timezone
from datetime import timedelta

class SessionTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            last_activity = request.session.get('last_activity')
            
            if last_activity:
                idle_time = timezone.now() - timezone.datetime.fromisoformat(last_activity)
                if idle_time > timedelta(seconds=settings.SESSION_IDLE_TIMEOUT):
                    logout(request)
                    return self.get_response(request)
            
            request.session['last_activity'] = timezone.now().isoformat()

        return self.get_response(request) 