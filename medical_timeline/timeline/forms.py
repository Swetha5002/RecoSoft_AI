from django import forms
from .models import MedicalProfile, MedicalEvent, EventAttachment
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
    
    class Meta:
        model = MedicalEvent
        fields = [
            'event_type', 'title', 'date', 'condition', 
            'hospital', 'doctor', 'total_cost', 
            'insurance_covered', 'status', 'summary'
        ]
        widgets = {
            'event_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'summary': forms.Textarea(attrs={'rows': 4}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        total_cost = cleaned_data.get('total_cost', 0)
        insurance_covered = cleaned_data.get('insurance_covered', 0)
        
        if insurance_covered > total_cost:
            raise forms.ValidationError(
                "Insurance covered amount cannot be greater than total cost."
            )
        
        return cleaned_data

class AttachmentForm(forms.ModelForm):
    class Meta:
        model = EventAttachment
        fields = ['file']
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            if file.size > 10 * 1024 * 1024:  # 10MB limit
                raise forms.ValidationError("File size must be under 10MB.")
        return file