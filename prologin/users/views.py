from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.views import logout, login as django_login_view
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse, reverse_lazy
from django.db.models import Prefetch, Q
from django.http import Http404
from django.http.response import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render, redirect
from django.template.base import Template, Context
from django.template.loader import get_template
from django.utils.http import is_safe_url
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.generic.base import View, RedirectView, TemplateView
from django.views.generic.detail import DetailView, SingleObjectMixin
from django.views.generic.edit import CreateView, UpdateView, FormView
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
import django.contrib.auth.forms
from django.views.generic.list import ListView
from hmac import compare_digest
from rules.contrib.views import PermissionRequiredMixin
from zinnia.models.author import Author

from prologin.email import send_email
from prologin.utils import absolute_site_url

import team.models
import users.forms
import users.models


@csrf_protect
@require_POST
@never_cache
def protected_logout(*args, **kwargs):
    return logout(*args, **kwargs)


def custom_login(request, *args, **kwargs):
    kwargs['template_name'] = 'users/login.html'
    kwargs['authentication_form'] = users.forms.ProloginAuthenticationForm
    if request.user.is_authenticated():
        return redirect('users:profile', pk=request.user.pk)
    return django_login_view(request, *args, **kwargs)


def auto_login(request, user):
    # Auto-login bullshit because we don't want to write our own backend
    from django.contrib.auth import load_backend, login
    if not hasattr(user, 'backend'):
        for backend in settings.AUTHENTICATION_BACKENDS:
            if user == load_backend(backend).get_user(user.pk):
                user.backend = backend
                break
    if hasattr(user, 'backend'):
        login(request, user)
        return True
    return False


class AnonymousRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return redirect('users:profile', pk=request.user.pk)
        return super().dispatch(request, *args, **kwargs)


class RegistrationView(AnonymousRequiredMixin, CreateView):
    model = get_user_model()
    form_class = users.forms.RegisterForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        response = super().form_valid(form)
        new_user = self.object
        activation = users.models.UserActivation.objects.register(new_user)
        url = absolute_site_url(self.request, reverse('users:activate', args=[activation.slug]))
        send_email("users/mails/activation", self.object.email, {'user': self, 'url': url})
        messages.success(self.request, _("Your account was created. We sent an email to %(mail)s "
                                         "so you can confirm your registration.") % {'mail': self.object.email})
        return response


class ActivationView(AnonymousRequiredMixin, SingleObjectMixin, RedirectView):
    model = users.models.UserActivation
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    permanent = False
    url = reverse_lazy('home')

    def get_object(self, queryset=None):
        slug = self.kwargs.get(self.slug_url_kwarg, None)
        return self.model.objects.activate(slug)

    def get(self, request, *args, **kwargs):
        try:
            activated_user = self.get_object()
            messages.success(request, _("Your account was activated. Enjoy your visit!"))
            if auto_login(request, activated_user):
                messages.success(request, _("You have been automatically logged in."))
            else:
                # If could not log the user in automatically, redirect to login
                self.url = 'users:login'
        except users.models.InvalidActivationError:
            messages.error(request, _("The activation link you provided is invalid or obsolete. "
                                      "If you created your account earlier than %(days)s days ago, "
                                      "you have to create a new one. You may use the same username "
                                      "and email though.") % {'days': settings.USER_ACTIVATION_EXPIRATION.days})
        return super().get(request, *args, **kwargs)


class ProfileView(DetailView):
    model = get_user_model()
    context_object_name = 'shown_user'
    template_name = 'users/profile.html'

    def get_queryset(self):
        self.author = Author(pk=self.kwargs[self.pk_url_kwarg])
        return super().get_queryset().prefetch_related(
            Prefetch('team_memberships',
                     queryset=team.models.TeamMember.objects.select_related('role__name')))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shown_user = context[self.context_object_name]
        context['shown_author'] = self.author
        context['see_private'] = self.request.user == shown_user or self.request.user.is_staff
        return context


class UpdateUserAsAdminView(UpdateView):
    model = get_user_model()
    context_object_name = 'edited_user'
    form_class_staff = None
    success_view = 'users:edit'

    def get_success_url(self):
        return reverse(self.success_view, args=[self.get_object().pk])

    def as_staff(self):
        return self.request.user != self.get_object()

    def get_form_class(self):
        if self.as_staff() and self.form_class_staff is not None:
            return self.form_class_staff
        return self.form_class

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['as_staff'] = self.as_staff()
        return context

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_staff and self.as_staff():
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)


class EditUserView(UpdateUserAsAdminView):
    template_name = 'users/edit.html'
    form_class = users.forms.UserProfileForm

    def get_form_kwargs(self):
        # Make important fields read-only during contest, for non-staff users
        # FIXME: use rules
        is_contest = not self.request.user.is_staff and self.request.current_edition.is_active
        kwargs = super().get_form_kwargs()
        kwargs['is_contest'] = is_contest
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, _("Changes saved."))
        return super().form_valid(form)


class PasswordFormMixin:
    """
    SetPasswordForm prototype is (user, *args, **kwargs) and does not use 'instance' kwarg.
    “Because fuck logic, that's why.”
        — Django
    """
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.pop('instance', None)
        return kwargs

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(self.get_object(), **self.get_form_kwargs())


class EditPasswordView(PasswordFormMixin, UpdateUserAsAdminView):
    template_name = 'users/edit_password.html'
    form_class = django.contrib.auth.forms.PasswordChangeForm
    form_class_staff = django.contrib.auth.forms.SetPasswordForm

    def form_valid(self, form):
        messages.success(self.request, _("New password saved."))
        return super().form_valid(form)


class PasswordResetView(AnonymousRequiredMixin, FormView):
    template_name = 'users/password_reset.html'
    form_class = users.forms.PasswordResetForm
    success_url = reverse_lazy('users:login')

    def form_valid(self, form):
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode
        from django.contrib.auth.tokens import default_token_generator

        email = form.cleaned_data['email']
        active_users = get_user_model().objects.filter(email__iexact=email, is_active=True)
        for user in active_users:
            # Make sure that no email is sent to a user that actually has
            # a password marked as unusable
            if not user.has_usable_password() and not user.legacy_md5_password:
                continue
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            url = absolute_site_url(self.request,
                                    reverse('users:password_reset_confirm', kwargs=dict(uidb64=uid, token=token)))
            send_email("users/mails/pswd_reset", user.email, {'user': user, 'url': url})

        messages.success(self.request,
                         _("You should receive an email at %(email)s in a few moments. "
                           "Please follow the instructions to complete the password reset.")
                         % {'email': email})
        return super().form_valid(form)


class PasswordResetConfirmView(AnonymousRequiredMixin, PasswordFormMixin, UpdateView):
    model = get_user_model()
    template_name = 'registration/password_reset_confirm.html'
    form_class = django.contrib.auth.forms.SetPasswordForm
    success_url = reverse_lazy('home')

    def get_object(self, queryset=None):
        from django.utils.encoding import force_text
        from django.utils.http import urlsafe_base64_decode
        from django.contrib.auth.tokens import default_token_generator
        uidb64 = self.kwargs['uidb64']
        token = self.kwargs['token']
        user = None
        try:
            uid = force_text(urlsafe_base64_decode(uidb64))
            user = get_user_model().objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, self.model.DoesNotExist):
            pass

        if user is not None and not default_token_generator.check_token(user, token):
            user = None
        if not user:
            raise Http404()
        return user

    def form_valid(self, form):
        user = self.get_object()
        messages.success(self.request, _("New password saved."))
        if auto_login(self.request, user):
            messages.success(self.request, _("You have been automatically logged in."))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['validlink'] = self.get_object() is not None
        return context


class UnsubscribeView(View):
    def get_user_token(self, req_params):
        try:
            user_id = req_params['uid']
            token = req_params['token']
        except KeyError:
            raise Http404()
        User = get_user_model()
        u = get_object_or_404(User, pk=user_id)
        if not compare_digest(token, u.unsubscribe_token):
            raise Http404()
        return u, token

    def get(self, request, *args, **kwargs):
        user, token = self.get_user_token(request.GET)
        return render(request, 'users/unsubscribe.html',
                {'unsubscribe_user': user, 'unsubscribe_token': token})

    def post(self, request, *args, **kwargs):
        user, _ = self.get_user_token(request.POST)
        user.allow_mailing = False
        user.save()
        return render(request, 'users/unsubscribe_confirm.html',
                {'unsubscribe_user': user})


class ImpersonateView(PermissionRequiredMixin, FormView):
    form_class = users.forms.ImpersonateForm
    permission_required = 'users.may_impersonate'
    error_message = _("Unable to complete impersonation: %(msg)s")

    def get(self, request, *args, **kwargs):
        raise Http404()

    def get_success_url(self):
        url = self.request.GET.get('next')
        if url and is_safe_url(url, host=settings.SITE_HOST):
            return url
        return '/'

    def form_valid(self, form):
        from hijack.helpers import is_authorized, login_user

        hijacked = form.cleaned_data['user']

        error = None
        if not hijacked.is_active:
            error = _("you cannot impersonate an inactive user.")
        elif not is_authorized(self.request.user, hijacked):
            error = _("you don't have the permission to impersonate this user.")

        if error:
            messages.error(self.request, self.error_message % {'msg': error})
            return redirect(self.get_success_url())

        login_user(self.request, hijacked)
        return super().form_valid(form)

    def form_invalid(self, form):
        # You can land here if JS is not enabled and there is no user or invalid form
        # Field errors can stay hidden because they can only be the result of malicious request crafting
        for error in form.non_field_errors():
            messages.error(self.request, self.error_message % {'msg': error})
        # Redirect without impersonating
        return super().form_valid(form)


class ImpersonateSearchView(PermissionRequiredMixin, ListView):
    model = get_user_model()
    paginate_by = 10
    permission_required = 'users.may_impersonate'

    def get_queryset(self):
        query = self.request.GET.get('q', '').strip()
        return users.forms.ImpersonateForm.search_users(query)

    def render_to_response(self, context, **response_kwargs):
        tpl = get_template('users/stub-impersonate-result.html')
        results = [
            {
                'id': user.pk,
                'username': user.username,
                'html': tpl.render(Context({'user': user})),
            }
            for user in self.get_queryset()]
        return JsonResponse(results, safe=False)
