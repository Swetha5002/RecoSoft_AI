from django.contrib import admin
from .models import MedicalProfile, MedicalEvent, EventAttachment

admin.site.register(MedicalProfile)
admin.site.register(MedicalEvent)
admin.site.register(EventAttachment)
