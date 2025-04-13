from django import forms
from .models import MedicalProfile, MedicalEvent, EventAttachment, EventReport
from django.contrib.auth.models import User
from django.utils import timezone

class MedicalProfileForm(forms.ModelForm):
    birth_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=True
    )
    
    class Meta:
        model = MedicalProfile
        fields = ['birth_date', 'blood_type', 'height', 'weight', 'profile_picture']
        widgets = {
            'blood_type': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def clean_profile_picture(self):
        picture = self.cleaned_data.get('profile_picture')
        if picture:
            if picture.size > 5 * 1024 * 1024:  # 5MB
                raise forms.ValidationError("Profile picture must be under 5MB")
        return picture

class MedicalEventForm(forms.ModelForm):
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        initial=timezone.now
    )
    voice_recording = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'accept': 'audio/*'})
    )

    class Meta:
        model = MedicalEvent
        fields = [
            'event_type', 'title', 'date', 'summary', 'voice_recording',
            'doctor', 'hospital', 'total_cost', 'insurance_covered'
        ]
        widgets = {
            'event_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'summary': forms.Textarea(attrs={'rows': 4}),
            'doctor': forms.TextInput(attrs={'class': 'form-control'}),
            'hospital': forms.TextInput(attrs={'class': 'form-control'}),
            'total_cost': forms.NumberInput(attrs={'class': 'form-control'}),
            'insurance_covered': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class AttachmentForm(forms.ModelForm):
    file = forms.FileField(widget=forms.ClearableFileInput())

    class Meta:
        model = EventReport
        fields = ['file']
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            if file.size > 10 * 1024 * 1024:  # 10MB limit
                raise forms.ValidationError("File size must be under 10MB.")
        return file