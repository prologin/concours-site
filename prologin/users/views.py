from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.shortcuts import redirect, render, get_object_or_404
from django.core.exceptions import SuspiciousOperation
from users.models import UserProfile, RegisterForm, ActivationToken, ProloginUser
from users.avatars import generate_avatar
from io import BytesIO as StringIO

def profile(request, slug):
    profile = get_object_or_404(UserProfile, slug=slug)
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
            pu = ProloginUser()
            print(form.cleaned_data)
            pu.register(form.cleaned_data['username'], form.cleaned_data['email'], form.cleaned_data['password'], form.cleaned_data['newsletter'])
            return redirect('/')
    autofill = {}
    for el in ['email', 'password']:
        if request.POST and form.cleaned_data[el]:
            print('data: %s: %s' % (el, form.cleaned_data[el]))
            autofill[el] = form.cleaned_data[el]
        else:
            autofill[el] = ''
    return render(request, 'users/register.html', {'register_form': form if form is not None else RegisterForm(),
                                                   'errors': None if form is None else form.errors,
                                                   'autofill': autofill,
                                                   })

def activate(request, username, code):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        raise SuspiciousOperation('Account activation: %s: invalid user' % username)

    try:
        token = ActivationToken.objects.get(slug=code)
    except ActivationToken.DoesNotExist:
        raise SuspiciousOperation('Account activation: User %s: invalid activation token' % user.username)

    if user.id != token.user.id:
        raise SuspiciousOperation('Account activation: User %s tried to activate his account using a token belonging to user %s.' % (user.username, token.user.username))

    user.is_active = True
    user.save()
    token.delete()

    return redirect('%s' % request.GET.get('next', '/'))
