from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Count, Sum, Avg, F
from django.db.models.functions import ExtractYear, ExtractMonth
from django.utils import timezone
from django.http import HttpResponse, Http404
import json
import secrets
from decimal import Decimal
from django.core.serializers.json import DjangoJSONEncoder
import speech_recognition as sr
from PIL import Image
import pytesseract

from .models import MedicalProfile, MedicalEvent, EventAttachment, EventReport
from .forms import MedicalProfileForm, MedicalEventForm, AttachmentForm

from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.utils import timezone
from django.contrib.auth import logout

def home(request):
    if request.method == 'POST' and 'logout' in request.POST:
        logout(request)
        return redirect('timeline:home')
        
    context = {
        'title': 'Welcome to Medical Timeline',
        'user': request.user
    }
    return render(request, 'timeline/home.html', context)

class SignUpView(CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('timeline:login')
    template_name = 'timeline/registration/signup.html'

    def form_valid(self, form):
        # Just save the user without creating profile
        # Profile will be created by the signal
        response = super().form_valid(form)
        messages.success(self.request, 'Account created successfully! Please login.')
        return response

@login_required
def index(request):
    profile = MedicalProfile.objects.filter(user=request.user).first()
    events = MedicalEvent.objects.filter(user=request.user).order_by('-date')

    # Debugging: Check for events without primary keys
    for event in events:
        if not event.pk:
            print(f"Event without PK: {event}")

    # Add statistics
    stats = {
        'total_events': events.count(),
        'total_cost': sum(event.total_cost for event in events),
        'insurance_covered': sum(event.insurance_covered for event in events),
        'event_types': events.values('event_type').annotate(count=Count('event_type'))
    }

    # Group events by year
    events_by_year = {}
    for event in events:
        year = event.date.year
        if year not in events_by_year:
            events_by_year[year] = []
        events_by_year[year].append(event)

    context = {
        'profile': profile,
        'events_by_year': events_by_year,
        'stats': stats,
    }
    return render(request, 'timeline/index.html', context)

@login_required
def share_timeline(request, user_id):
    user_profile = get_object_or_404(MedicalProfile, user_id=user_id)
    if request.method == 'POST':
        # Generate a unique sharing link
        share_token = generate_share_token()
        user_profile.share_token = share_token
        user_profile.save()
        share_url = request.build_absolute_uri(
            reverse('timeline:shared-timeline', kwargs={'token': share_token})
        )
        return JsonResponse({'share_url': share_url})
    return JsonResponse({'error': 'Invalid request'}, status=400)

def shared_timeline(request, token):
    """View for displaying a shared timeline"""
    try:
        # Find the profile with matching share token
        profile = get_object_or_404(MedicalProfile, share_token=token)
        events = MedicalEvent.objects.filter(user=profile.user).order_by('-date')
        
        # Add statistics
        stats = {
            'total_events': events.count(),
            'total_cost': sum(event.total_cost for event in events),
            'insurance_covered': sum(event.insurance_covered for event in events),
            'event_types': events.values('event_type').annotate(count=Count('event_type'))
        }
        
        # Pagination
        paginator = Paginator(events, 10)
        page = request.GET.get('page')
        events_paginated = paginator.get_page(page)
        
        # Group events by year
        events_by_year = {}
        for event in events_paginated:
            year = event.date.year
            if year not in events_by_year:
                events_by_year[year] = []
            events_by_year[year].append(event)
        
        context = {
            'profile': profile,
            'events_by_year': events_by_year,
            'stats': stats,
            'page_obj': events_paginated,
            'is_shared': True  # Flag to modify template behavior
        }
        return render(request, 'timeline/shared_timeline.html', context)
    except (MedicalProfile.DoesNotExist, ValueError):
        raise Http404("Timeline not found or sharing has expired")

def generate_share_token():
    """Generate a unique token for timeline sharing"""
    return secrets.token_urlsafe(32)

class MedicalProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = MedicalProfile
    form_class = MedicalProfileForm
    template_name = 'timeline/profile_form.html'
    success_url = reverse_lazy('timeline:index')
    
    def get_object(self, queryset=None):
        # Get or create profile for the current user
        obj, created = MedicalProfile.objects.get_or_create(user=self.request.user)
        return obj
    
    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)

class MedicalEventCreateView(LoginRequiredMixin, CreateView):
    model = MedicalEvent
    form_class = MedicalEventForm
    template_name = 'timeline/event_form.html'
    success_url = reverse_lazy('timeline:index')

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_add'] = True
        return context

class MedicalEventUpdateView(LoginRequiredMixin, UpdateView):
    model = MedicalEvent
    form_class = MedicalEventForm
    template_name = 'timeline/event_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Ensure users can only edit their own events
        obj = self.get_object()
        if obj.user != self.request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse_lazy('timeline:event-detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Event updated successfully!')
        return super().form_valid(form)

class MedicalEventDetailView(LoginRequiredMixin, DetailView):
    model = MedicalEvent
    template_name = 'timeline/partials/event_detail.html'
    context_object_name = 'event'  # Add this line
    
    def dispatch(self, request, *args, **kwargs):
        # Ensure users can only view their own events
        obj = self.get_object()
        if obj.user != self.request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event'] = self.get_object()  # Explicitly add event to context
        return context

class MedicalEventDeleteView(LoginRequiredMixin, DeleteView):
    model = MedicalEvent
    template_name = 'timeline/event_confirm_delete.html'
    
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.user != self.request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        messages.success(self.request, 'Event deleted successfully!')
        return reverse_lazy('timeline:index')

@login_required
def upload_attachment(request, event_id):
    event = get_object_or_404(MedicalEvent, pk=event_id, user=request.user)
    
    if request.method == 'POST':
        form = AttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.event = event
            attachment.save()
            return JsonResponse({
                'success': True,
                'filename': attachment.filename(),
                'url': attachment.file.url,
                'id': attachment.id
            })
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def delete_attachment(request, attachment_id):
    attachment = get_object_or_404(EventAttachment, pk=attachment_id, event__user=request.user)
    attachment.delete()
    return JsonResponse({'success': True})

class DecimalEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

@login_required
def health_analytics(request):
    # Get user's events
    events = MedicalEvent.objects.filter(user=request.user)
    
    # Time-based Analysis
    events_by_year = list(events.annotate(year=ExtractYear('date'))
        .values('year')
        .annotate(count=Count('id'))
        .order_by('year'))
    
    # Location Analysis
    location_stats = list(events.exclude(hospital='')
        .values('hospital')
        .annotate(count=Count('id'))
        .order_by('-count')[:5])
    
    # Cost Analysis
    cost_by_type = list(events.values('event_type')
        .annotate(
            total_cost=Sum('total_cost'),
            event_count=Count('id')
        ).annotate(
            avg_cost=F('total_cost') / F('event_count')
        ).order_by('-total_cost'))
    
    # Condition Analysis with percentages
    condition_stats = events.exclude(condition='').values('condition').annotate(count=Count('id')).order_by('-count')[:10]
    total_conditions = sum(stat['count'] for stat in condition_stats)
    
    condition_stats_with_percent = [
        {
            'condition': stat['condition'],
            'count': stat['count'],
            'percentage': (stat['count'] / total_conditions * 100) if total_conditions > 0 else 0
        }
        for stat in condition_stats
    ]
    
    # Insurance Coverage Analysis
    total_cost = events.aggregate(total=Sum('total_cost'))['total'] or 0
    total_covered = events.aggregate(covered=Sum('insurance_covered'))['covered'] or 0
    
    insurance_data = {
        'total_cost': float(total_cost),
        'total_covered': float(total_covered),
        'out_of_pocket': float(total_cost - total_covered)
    }
    insurance_coverage_rate = (total_covered / total_cost * 100) if total_cost > 0 else 0
    
    # Event Type Distribution
    type_distribution = list(events.values('event_type')
        .annotate(count=Count('id'))
        .order_by('-count'))
    
    context = {
        'events_by_year': json.dumps(events_by_year, cls=DecimalEncoder),
        'location_stats': json.dumps(location_stats, cls=DecimalEncoder),
        'cost_by_type': json.dumps(cost_by_type, cls=DecimalEncoder),
        'insurance_data': json.dumps(insurance_data, cls=DecimalEncoder),
        'insurance_coverage_rate': insurance_coverage_rate,
        'type_distribution': json.dumps(type_distribution, cls=DecimalEncoder),
        'condition_stats': condition_stats_with_percent
    }
    
    return render(request, 'timeline/analytics.html', context)

def public_health_analytics(request):
    # Get all events (not filtered by user)
    events = MedicalEvent.objects.all()

    # Time-based Analysis (Yearly and Monthly)
    events_by_year = list(events.annotate(year=ExtractYear('date'))
        .values('year')
        .annotate(count=Count('id'))
        .order_by('year'))

    events_by_month = list(events.annotate(month=ExtractMonth('date'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month'))

    # Location Analysis
    location_stats = list(events.exclude(hospital='')
        .values('hospital')
        .annotate(count=Count('id'))
        .order_by('-count')[:5])

    # Cost Analysis
    cost_by_type = list(events.values('event_type')
        .annotate(
            total_cost=Sum('total_cost'),
            event_count=Count('id')
        ).annotate(
            avg_cost=F('total_cost') / F('event_count')
        ).order_by('-total_cost'))

    # Top Conditions
    condition_stats = events.exclude(condition='').values('condition').annotate(count=Count('id')).order_by('-count')[:10]
    total_conditions = sum(stat['count'] for stat in condition_stats)

    condition_stats_with_percent = [
        {
            'condition': stat['condition'],
            'count': stat['count'],
            'percentage': (stat['count'] / total_conditions * 100) if total_conditions > 0 else 0
        }
        for stat in condition_stats
    ]

    # Insurance Coverage Analysis
    total_cost = events.aggregate(total=Sum('total_cost'))['total'] or 0
    total_covered = events.aggregate(covered=Sum('insurance_covered'))['covered'] or 0

    insurance_data = {
        'total_cost': float(total_cost),
        'total_covered': float(total_covered),
        'out_of_pocket': float(total_cost - total_covered)
    }
    insurance_coverage_rate = (total_covered / total_cost * 100) if total_cost > 0 else 0

    # Event Type Distribution
    type_distribution = list(events.values('event_type')
        .annotate(count=Count('id'))
        .order_by('-count'))

    context = {
        'events_by_year': json.dumps(events_by_year, cls=DecimalEncoder),
        'events_by_month': json.dumps(events_by_month, cls=DecimalEncoder),
        'location_stats': json.dumps(location_stats, cls=DecimalEncoder),
        'cost_by_type': json.dumps(cost_by_type, cls=DecimalEncoder),
        'insurance_data': json.dumps(insurance_data, cls=DecimalEncoder),
        'insurance_coverage_rate': insurance_coverage_rate,
        'type_distribution': json.dumps(type_distribution, cls=DecimalEncoder),
        'condition_stats': condition_stats_with_percent
    }

    return render(request, 'timeline/public_analytics.html', context)

