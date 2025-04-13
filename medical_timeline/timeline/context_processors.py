from .models import MedicalProfile

def user_profile(request):
    if request.user.is_authenticated:
        try:
            profile = MedicalProfile.objects.get(user=request.user)
        except MedicalProfile.DoesNotExist:
            profile = None
        return {'profile': profile}
    return {}