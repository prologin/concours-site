from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, REDIRECT_FIELD_NAME, login
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import RedirectView
from django.views.generic.detail import DetailView, SingleObjectMixin
from django.views.generic.edit import CreateView, UpdateView, FormView
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
import django.contrib.auth.forms

from prologin.email import send_email
from prologin.utils import absolute_site_url

import users.forms
import users.models


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


class LoginView(FormView):
    template_name = 'users/login.html'
    form_class = AuthenticationForm
    redirect_field_name = REDIRECT_FIELD_NAME

    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        return super(LoginView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        """
        Same as django.views.generic.edit.ProcessFormView.get(), but adds test cookie stuff
        """
        self.set_test_cookie()
        return super(LoginView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['password_reset_form'] = users.forms.PasswordResetForm()
        return context

    def form_valid(self, form):
        """
        The user has provided valid credentials (this was checked in AuthenticationForm.is_valid()). So now we
        can check the test cookie stuff and log him in.
        """
        self.check_and_delete_test_cookie()
        login(self.request, form.get_user())
        return super(LoginView, self).form_valid(form)

    def form_invalid(self, form):
        """
        The user has provided invalid credentials (this was checked in AuthenticationForm.is_valid()). So now we
        set the test cookie again and re-render the form with errors.
        """
        self.set_test_cookie()
        return super(LoginView, self).form_invalid(form)

    def set_test_cookie(self):
        self.request.session.set_test_cookie()

    def check_and_delete_test_cookie(self):
        if self.request.session.test_cookie_worked():
            self.request.session.delete_test_cookie()
            return True
        return False


class RegistrationView(CreateView):
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


class ActivationView(SingleObjectMixin, RedirectView):
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
        except users.models.InvalidActivationError as e:
            messages.error(request, _("The activation link you provided is invalid or obsolete. "
                                      "If you created your account earlier than %(days)s days ago, "
                                      "you have to create a new one. You may use the same username "
                                      "and email though.") % {'days': settings.ACCOUNT_ACTIVATION_DAYS})
        return super().get(request, *args, **kwargs)


class ProfileView(DetailView):
    model = get_user_model()
    context_object_name = 'shown_user'
    template_name = 'users/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shown_user = self.get_object()
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
    initial = {'allow_mailing': True}

    def form_valid(self, form):
        messages.success(self.request, _("Changes saved."))
        return super().form_valid(form)


class PasswordFormMixin(UpdateView):
    """
    SetPasswordForm prototype is (user, *args, **kwargs) and does not use 'instance' kwarg.
    “Because fuck logic, that's why.”
        — Django
    """
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.pop('instance', None)
        return kwargs

    def get_form(self, form_class):
        return form_class(self.get_object(), **self.get_form_kwargs())


class EditPasswordView(PasswordFormMixin, UpdateUserAsAdminView):
    template_name = 'users/edit_password.html'
    form_class = django.contrib.auth.forms.PasswordChangeForm
    form_class_staff = django.contrib.auth.forms.SetPasswordForm

    def form_valid(self, form):
        messages.success(self.request, _("New password saved."))
        return super().form_valid(form)


class PasswordResetView(FormView):
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
            if not user.has_usable_password():
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


class PasswordResetConfirmView(PasswordFormMixin, UpdateView):
    model = get_user_model()
    template_name = 'registration/password_reset_confirm.html'
    form_class = django.contrib.auth.forms.SetPasswordForm
    success_url = reverse('home')

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
        return user

    def form_valid(self, form):
        messages.success(self.request, _("New password saved."))
        if auto_login(self.request, self.get_object()):
            messages.success(self.request, _("You have been automatically logged in."))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['validlink'] = self.get_object() is not None
        return context
