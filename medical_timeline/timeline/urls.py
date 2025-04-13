from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.contrib.auth import views as auth_views
from .views import SignUpView, public_health_analytics
from timeline.models import MedicalEvent

app_name = 'timeline'

urlpatterns = [
    path('', views.home, name='home'),  # New landing page
    path('timeline/', views.index, name='index'),

    path('accounts/login/', auth_views.LoginView.as_view(template_name='timeline/registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='timeline:home'), name='logout'),
    path('accounts/signup/', SignUpView.as_view(), name='signup'),
    
    # Profile
    path('profile/', views.MedicalProfileUpdateView.as_view(), name='profile'),
    
    # Events
    path('events/add/', views.MedicalEventCreateView.as_view(), name='event-add'),
    path('events/<int:pk>/', views.MedicalEventDetailView.as_view(), name='event-detail'),
    path('events/<int:pk>/edit/', views.MedicalEventUpdateView.as_view(), name='event-edit'),
    path('events/<int:pk>/delete/', views.MedicalEventDeleteView.as_view(), name='event-delete'),
    
    # Attachments
    path('events/<int:event_id>/upload/', views.upload_attachment, name='upload-attachment'),
    path('attachments/<int:attachment_id>/delete/', views.delete_attachment, name='delete-attachment'),

    # Sharing
    path('share/<int:user_id>/', views.share_timeline, name='share-timeline'),
    path('shared/<str:token>/', views.shared_timeline, name='shared-timeline'),

    # Analytics
    path('analytics/', views.health_analytics, name='analytics'),
    path('public-analytics/', public_health_analytics, name='public-analytics'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

MedicalEvent.objects.all().count()  # Should be greater than 0