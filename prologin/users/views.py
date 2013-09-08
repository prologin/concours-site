from django.contrib.auth import logout
from django.shortcuts import redirect, render, get_object_or_404
from users.models import UserProfile

def logout_view(request):
    logout(request)
    return redirect('%s' % request.GET.get('next', '/'))

def profile(request, short_name):
    profile = get_object_or_404(UserProfile, short_name=short_name)
    return render(request, 'users/profile.html', {'profile': profile})
