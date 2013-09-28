from django.contrib.auth import logout
from django.http import HttpResponse, Http404
from django.shortcuts import redirect, render, get_object_or_404
from users.models import UserProfile, RegisterForm
from users.avatars import generate_avatar
from io import BytesIO as StringIO

def profile(request, short_name):
    profile = get_object_or_404(UserProfile, short_name=short_name)
    return render(request, 'users/profile.html', {'profile': profile})

def logout_view(request):
    logout(request)
    return redirect('%s' % request.GET.get('next', '/'))

def register_view(request):
    if request.user.is_authenticated():
         return redirect('/')
    form = None
    if request.POST:
        form = RegisterForm(request.POST)
        if form.is_valid():
            return redirect(reverse('/'))
    return render(request, 'users/register.html', {'register_form': form if form is not None else RegisterForm(),
                                                   'errors': None if form is None else form.errors,
                                                   })
