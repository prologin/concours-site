from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render, get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.views.generic.detail import DetailView
import django.contrib.auth.forms
import users.forms
import users.models


class ProfileView(DetailView):
    model = get_user_model()
    context_object_name = 'shown_user'
    template_name = 'users/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shown_user = self.get_object()
        context['see_private'] = self.request.user == shown_user or self.request.user.is_staff
        return context


def register_view(request):
    if request.user.is_authenticated():
        return redirect('/')

    form = users.forms.RegisterForm()
    if request.POST:
        form = users.forms.RegisterForm(request.POST)
        if form.is_valid():
            # Create user
            user = get_user_model().objects.create_user(
                form.cleaned_data['username'],
                form.cleaned_data['email'],
                form.cleaned_data['password'])
            user.is_active = False
            user.save()
            # Create activation token
            token = users.models.ActivationToken.objects.create_token(user)
            token.save()
            # Send activation email
            user.send_activation_email(token)
            messages.success(request, _(
                "Votre compte a été créé. Nous avons envoyé un email à %(mail)s "
                "pour que vous puissiez valider votre inscription.") % {'mail': user.email})
            return redirect('home')

    return render(request, 'users/register.html', {
        'form': form,
        'next': request.GET.get('next', '/'),
    })


def activate(request, user_id, code):
    user = get_object_or_404(get_user_model(), pk=user_id)

    try:
        token = users.models.ActivationToken.objects.get(slug=code)
    except users.models.ActivationToken.DoesNotExist:
        messages.error(request, _("Le lien d'activation que vous avez utilisé est invalide. Vérifiez qu'il n'y a pas d'erreur."))
        return redirect('home')

    if not token.is_valid():
        # TODO: ouais, et du coup le mec il fait quoi ? il crée un second compte ? #genius
        messages.error(request, _("Le lien d'activation que vous avez utilisé est périmé."))
        return redirect('home')

    user = token.user
    user.is_active = True
    user.save()
    token.delete()

    messages.success(request, _("Votre compte est maintenant activé. Merci !"))
    return redirect('home')


def edit_user(request, user_id):
    edited_user = get_object_or_404(get_user_model(), pk=user_id)

    as_staff = request.user != edited_user
    if not request.user.is_staff and as_staff:
        raise PermissionDenied()

    user_form = users.forms.UserSimpleForm(data=request.POST or None, instance=edited_user)

    if request.method == 'POST':
        if user_form.is_valid():
            user_form.save()
            messages.success(request, _("Modifications enregistrées."))
            return redirect('users:edit', user_id=edited_user.pk)

    return render(request, 'users/edit.html', {'edited_user': edited_user, 'form': user_form, 'as_staff': as_staff})


def edit_user_password(request, user_id):
    edited_user = get_object_or_404(get_user_model(), pk=user_id)

    form_cls = django.contrib.auth.forms.PasswordChangeForm
    as_staff = False
    if request.user != edited_user:
        if not request.user.is_staff:
            raise PermissionDenied()
        as_staff = True
        form_cls = django.contrib.auth.forms.AdminPasswordChangeForm

    form = form_cls(data=request.POST or None, user=edited_user)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, _("Mot de passe modifié."))
            return redirect('users:edit', user_id=edited_user.pk)

    return render(request, 'users/edit_password.html', {'edited_user': edited_user, 'form': form, 'as_staff': as_staff})
