from users.models import UserProfile, RegisterForm, ActivationToken
from django.shortcuts import redirect, render, get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import SuspiciousOperation
from django.core.exceptions import PermissionDenied
from django.views.generic.detail import DetailView
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.contrib import messages
from users.models import *
from io import BytesIO as StringIO

class ProfileView(DetailView):
    model = User
    context_object_name = 'usr'
    template_name = 'users/profile.html'

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
            u = User.objects.create_user(form.cleaned_data['username'], form.cleaned_data['email'], form.cleaned_data['password'])
            u.is_active = False
            u.save()
            p = UserProfile.objects.get(user_id=u.id)
            p.newsletter = form.cleaned_data['newsletter']
            p.save()
            messages.success(request, _('You have been registered, please check your emails.'))
            return redirect(request.GET.get('next', '/'))
    autofill = {}
    for el in ['email', 'password']:
        if request.POST and el in request.POST:
            autofill[el] = request.POST[el]
        else:
            autofill[el] = ''
    return render(request, 'users/register.html', {
        'register_form': form if form is not None else RegisterForm(),
        'errors': None if form is None else form.errors,
        'autofill': autofill,
        'next': request.GET.get('next', '/'),
    })

def activate(request, user_id, code):
    user = get_object_or_404(User, pk=user_id)

    try:
        token = ActivationToken.objects.get(slug=code)
    except ActivationToken.DoesNotExist:
        raise SuspiciousOperation('Account activation: User %s: invalid activation token' % user.username)

    if user.id != token.user.id:
        raise SuspiciousOperation('Account activation: User %s tried to activate his account using a token belonging to user %s.' % (user.username, token.user.username))

    user.is_active = True
    user.save()
    token.delete()

    return redirect(request.GET.get('next', '/'))

def edit_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.user.id != user.id and not request.user.is_staff:
        raise PermissionDenied

    if request.method == 'POST':
        profile_form = UserProfileForm(request.POST, instance=user.profile)
        user_form = UserSimpleForm(request.POST, instance=user)
        if profile_form.is_valid() and user_form.is_valid():
            profile_form.save()
            user_form.save()
            messages.success(request, _('Modification saved.'))
            return redirect('users:edit', user_id=user.id)
    profile_form = UserProfileForm(instance=user.profile)
    user_form = UserSimpleForm(instance=user)
    return render(request, 'users/edit.html', {'usr': user, 'profile_form': profile_form, 'user_form': user_form})
