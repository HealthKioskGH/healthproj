from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import home_view
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib.auth import views as auth_views
from accounts.views import CustomPasswordResetConfirmView
from patients import views
from allauth.account.views import EmailVerificationSentView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('accounts/', include('accounts.urls')),
    path('patients/', include('patients.urls')),
    path('doctors/', include('doctors.urls')),
    path('appointments/', include('appointments.urls')),
    path('notifications/', include('notifications.urls')),
    path('admin-dashboard/', include('admin_dashboard.urls')),
    
    # Override the default password reset confirm view
    path(
        'accounts/reset/<uidb64>/<token>/',
        CustomPasswordResetConfirmView.as_view(),
        name='password_reset_confirm'
    ),
    
    # Keep this at the end to not override our custom URL
    path('accounts/email/verification/sent/', 
         EmailVerificationSentView.as_view(template_name='account/verification_sent.html'),
         name='account_email_verification_sent'),
    path('accounts/', include('allauth.urls')),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += staticfiles_urlpatterns() 