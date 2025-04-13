from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
import os

def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.mp3', '.wav', '.doc', '.docx', '.txt']
    if not ext.lower() in valid_extensions:
        raise ValidationError('Unsupported file type.')

class MedicalProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    birth_date = models.DateField(null=True, blank=True)  # Made optional
    blood_type = models.CharField(
        max_length=5, 
        choices=[
            ('A+', 'A+'), ('A-', 'A-'),
            ('B+', 'B+'), ('B-', 'B-'),
            ('AB+', 'AB+'), ('AB-', 'AB-'),
            ('O+', 'O+'), ('O-', 'O-'),
        ],
        null=True,
        blank=True
    )
    height = models.PositiveIntegerField(help_text="Height in cm", null=True, blank=True)
    weight = models.PositiveIntegerField(help_text="Weight in kg", null=True, blank=True)
    profile_picture = models.ImageField(
        upload_to='profile_pics/', 
        null=True, 
        blank=True, 
        default='profile_pics/default-profile.jpg'  # Default profile picture
    )
    share_token = models.CharField(max_length=100, blank=True, null=True, unique=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()}'s Medical Profile"
    
    def get_absolute_url(self):
        return reverse('profile')

    def generate_share_token(self):
        import uuid
        self.share_token = str(uuid.uuid4())
        self.save()
        return self.share_token

class MedicalEvent(models.Model):
    EVENT_TYPES = [
        ('checkup', 'Checkup/Physical'),
        ('vaccination', 'Vaccination'),
        ('surgery', 'Surgery'),
        ('illness', 'Illness'),
        ('injury', 'Injury'),
        ('medication', 'Medication'),
        ('test', 'Test/Procedure'),
    ]
    
    STATUS_CHOICES = [
        ('resolved', 'Resolved'),
        ('ongoing', 'Ongoing'),
        ('chronic', 'Chronic'),
        ('preventive', 'Preventive'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    title = models.CharField(max_length=200)
    date = models.DateField(default=timezone.now)
    condition = models.CharField(max_length=200, blank=True, null=True)
    hospital = models.CharField(max_length=200, blank=True, null=True)
    doctor = models.CharField(max_length=200, blank=True, null=True)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    insurance_covered = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='resolved')
    summary = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    voice_recording = models.FileField(
        upload_to='voice_recordings/',
        validators=[validate_file_extension],
        blank=True,
        null=True
    )
    reports = models.ManyToManyField(
        'EventReport',
        blank=True,
        related_name='related_events'  # Set a unique related_name
    )
    generated_report = models.TextField(blank=True, null=True)  # New field for the default report
    consolidated_report = models.TextField(blank=True, null=True)  # Field for the consolidated report
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('timeline:event-detail', kwargs={'pk': self.pk})
    
    def get_edit_url(self):
        return reverse('timeline:event-edit', kwargs={'pk': self.pk})
    
    def get_delete_url(self):
        return reverse('timeline:event-delete', kwargs={'pk': self.pk})
    
    def get_event_class(self):
        """Return CSS class based on event type"""
        if self.event_type == 'checkup':
            return 'checkup'
        elif self.event_type == 'surgery':
            return 'surgery'
        elif self.event_type == 'illness':
            return 'illness'
        return ''

class EventAttachment(models.Model):
    event = models.ForeignKey(MedicalEvent, related_name='attachments', on_delete=models.CASCADE)
    file = models.FileField(
        upload_to='event_attachments/',
        validators=[validate_file_extension]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
        
    def __str__(self):
        return f"Attachment for {self.event.title}"
    
    def filename(self):
        return self.file.name.split('/')[-1]

class EventReport(models.Model):
    event = models.ForeignKey(
        MedicalEvent,
        on_delete=models.CASCADE,
        related_name='event_reports'
    )
    file = models.FileField(
        upload_to='event_reports/',  # Store files in media/event_reports/
        validators=[validate_file_extension]
    )
    extracted_text = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report for {self.event.title}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        MedicalProfile.objects.create(
            user=instance,
            birth_date=timezone.now().date(),
            blood_type='A+',
            height=170,
            weight=70,
        )

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.medicalprofile.save()
    except MedicalProfile.DoesNotExist:
        MedicalProfile.objects.create(
            user=instance,
            birth_date=timezone.now().date(),
            blood_type='A+',
            height=170,
            weight=70,
        )