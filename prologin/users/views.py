from django.conf import settings
from django.contrib import messages, auth
from django.http import Http404, HttpResponse
from django.http.response import JsonResponse, StreamingHttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render, redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.http import is_safe_url
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.views.generic.base import View, RedirectView
from django.views.generic.detail import DetailView, SingleObjectMixin
from django.views.generic.edit import CreateView, UpdateView, FormView, ModelFormMixin, FormMixin
from django.views.generic.list import ListView
from hmac import compare_digest
from rules.contrib.views import PermissionRequiredMixin
from urllib.parse import quote as url_quote
from wsgiref.util import FileWrapper

from prologin.utils import absolute_site_url
import contest.models
import users.forms
import users.models
import users.takeout


def auto_login(request, user):
    # Auto-login bullshit because we don't want to write our own backend
    if not hasattr(user, 'backend'):
        for backend in settings.AUTHENTICATION_BACKENDS:
            if user == auth.load_backend(backend).get_user(user.pk):
                user.backend = backend
                break
    if hasattr(user, 'backend'):
        auth.login(request, user)
        return True
    return False


def send_activation_email(user, request=None):
    from django.test import RequestFactory
    from prologin.email import send_email
    request = request or RequestFactory().generic('get', '/', secure=settings.SITE_BASE_URL.startswith('https'))
    activation = users.models.UserActivation.objects.register(user)
    url = absolute_site_url(request, reverse('users:activate', args=[activation.slug]))
    send_email("users/mails/activation", user.email, {'user': user, 'url': url})


class AnonymousRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)


class LoginView(auth.views.LoginView):
    template_name = 'users/login.html'
    authentication_form = users.forms.AuthenticationForm


@method_decorator([require_POST, csrf_protect, never_cache], name='dispatch')
class LogoutView(auth.views.LogoutView):
    next_page = reverse_lazy('home')


class RegistrationView(AnonymousRequiredMixin, CreateView):
    model = auth.get_user_model()
    form_class = users.forms.RegisterForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('home')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)


    def form_valid(self, form):
        response = super().form_valid(form)
        send_activation_email(self.object, request=self.request)
        messages.success(self.request,
                         _("Your account was created. We sent an email to %(mail)s so you can confirm your "
                           "registration.") % {'mail': self.object.email},
                         extra_tags='modal')
        return response


class ActivationView(AnonymousRequiredMixin, SingleObjectMixin, RedirectView):
    model = users.models.UserActivation
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    permanent = False
    pattern_name = 'home'

    def get_object(self, queryset=None):
        slug = self.kwargs.get(self.slug_url_kwarg, None)
        return self.model.objects.activate(slug)

    def get_redirect_url(self, *args, **kwargs):
        return super().get_redirect_url() + '?activated'

    def get(self, request, *args, **kwargs):
        try:
            activated_user = self.get_object()
            messages.success(request, _("Your account was activated. Enjoy your visit!"), extra_tags='modal')
            if not auto_login(request, activated_user):
                # If could not log the user in automatically, redirect to login
                self.url = 'users:login'
        except users.models.InvalidActivationError:
            messages.error(request, _("The activation link you provided is invalid or obsolete. "
                                      "If you created your account earlier than %(days)s days ago, "
                                      "you have to create a new one. You may use the same username "
                                      "and email though.") % {'days': settings.USER_ACTIVATION_EXPIRATION.days})
        return super().get(request, *args, **kwargs)


class CanEditProfileMixin:
    def can_edit_profile(self):
        # request user is privileged OR subject user can edit profile
        return (self.request.user.has_perm('users.edit-during-contest')
                or self.get_object().can_edit_profile(self.request.current_edition))


class ProfileView(CanEditProfileMixin, DetailView):
    model = auth.get_user_model()
    context_object_name = 'shown_user'
    template_name = 'users/profile.html'

    def get_queryset(self):
        from zinnia.models.author import Author
        self.author = Author(pk=self.kwargs[self.pk_url_kwarg])
        return super().get_queryset().prefetch_related('team_memberships')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shown_user = context[self.context_object_name]
        context['shown_author'] = self.author
        context['see_private'] = self.request.user == shown_user or self.request.user.is_staff
        return context

    def get(self, request, *args, **kwargs):
        result = super().get(request, *args, **kwargs)
        if not self.object.is_active and not self.request.user.is_staff:
            raise Http404()
        return result


class DownloadFinalHomeView(PermissionRequiredMixin, DetailView):
    permission_required = 'contest.can_download_home'
    model = contest.models.Contestant

    def get_object(self, queryset=None):
        return (queryset or self.get_queryset()).get(
            edition__year=self.kwargs['year'],
            user__pk=self.kwargs['pk'])

    def get(self, request, *args, **kwargs):
        super().get(request, *args, **kwargs)

        contestant = self.get_object()
        if not contestant.has_home:
            raise Http404()

        path = contestant.home_path
        response = StreamingHttpResponse(FileWrapper(open(path, 'rb')), content_type='application/x-gzip')
        response['Content-Length'] = contestant.home_size
        response['Content-Disposition'] = "attachment; filename={}".format(contestant.home_filename)
        return response


class EditUserView(PermissionRequiredMixin, CanEditProfileMixin, UpdateView):
    model = auth.get_user_model()
    form_class = users.forms.UserProfileForm
    template_name = 'users/edit.html'
    context_object_name = 'edited_user'
    permission_required = 'users.edit'

    def get_success_url(self):
        return reverse('users:edit', args=[self.get_object().pk])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['can_edit_profile'] = self.can_edit_profile()
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
    form_class = auth.forms.PasswordChangeForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.pop('instance', None)
        return kwargs

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(self.get_object(), **self.get_form_kwargs())


class EditPasswordView(PermissionRequiredMixin, PasswordFormMixin, UpdateView):
    model = auth.get_user_model()
    template_name = 'users/edit_password.html'
    context_object_name = 'edited_user'
    permission_required = 'users.edit'

    def form_valid(self, form):
        ret = super().form_valid(form)
        # from django.contrib.auth.views: log out from other sessions
        auth.update_session_auth_hash(self.request, self.object)
        messages.success(self.request, _("New password saved."))
        return ret


class PasswordResetView(AnonymousRequiredMixin, FormView):
    template_name = 'users/password_reset.html'
    form_class = users.forms.PasswordResetForm
    success_url = reverse_lazy('users:login')

    def form_valid(self, form):
        from prologin.email import send_email
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode
        from django.contrib.auth.tokens import default_token_generator

        email = form.cleaned_data['email']
        active_users = auth.get_user_model().objects.filter(email__iexact=email, is_active=True)
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
    model = auth.get_user_model()
    template_name = 'registration/password_reset_confirm.html'
    form_class = auth.forms.SetPasswordForm
    success_url = reverse_lazy('home')

    def get_object(self, queryset=None):
        from django.utils.encoding import force_text
        from django.utils.http import urlsafe_base64_decode
        from django.contrib.auth.tokens import default_token_generator
        uidb64 = self.kwargs['uidb64']
        token = self.kwargs['token']
        try:
            uid = force_text(urlsafe_base64_decode(uidb64))
            user = auth.get_user_model().objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, self.model.DoesNotExist):
            raise Http404()

        if not default_token_generator.check_token(user, token):
            raise Http404()

        return user

    def form_valid(self, form):
        user = form.save()
        messages.success(self.request, _("New password saved."))
        if auto_login(self.request, user):
            messages.success(self.request, _("You have been automatically logged in."))
        return super(ModelFormMixin, self).form_valid(form)


class UnsubscribeView(View):
    def get_user_token(self, req_params):
        try:
            user_id = int(req_params['uid'])
            token = req_params['token']
        except (KeyError, ValueError):
            raise Http404()

        User = auth.get_user_model()
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


class ImpersonateView(PermissionRequiredMixin, UpdateView):
    model = auth.get_user_model()
    fields = []

    def has_permission(self):
        from hijack.helpers import is_authorized
        return is_authorized(self.request.user, self.get_object())

    def get_success_url(self):
        url = self.request.GET.get('next')
        if url and is_safe_url(url, host=settings.SITE_HOST):
            return url
        return '/'

    def form_valid(self, form):
        from hijack.helpers import login_user
        login_user(self.request, self.get_object())
        return super(ModelFormMixin, self).form_valid(form)


class UserSearchSuggestView(PermissionRequiredMixin, ListView):
    model = auth.get_user_model()
    paginate_by = 10
    permission_required = 'users.search'

    def get_queryset(self):
        query = self.request.GET.get('q', '').strip()
        return users.models.search_users(query).order_by('-is_active', 'username')[:self.paginate_by]

    def render_to_response(self, context, **response_kwargs):
        results = [{
            'id': user.pk,
            'username': user.username,
            'url': reverse('users:profile', args=[user.pk]),
            'html': render_to_string(
                'users/stub-search-result.html',
                {'user': user, 'request': self.request},
                self.request),
        } for user in self.get_queryset()]
        return JsonResponse(results, safe=False)


class DeleteUserView(PermissionRequiredMixin, CanEditProfileMixin, UpdateView):
    model = auth.get_user_model()
    form_class = users.forms.ConfirmDeleteUserForm
    permission_required = 'users.delete'
    context_object_name = 'delete_user'
    success_url = reverse_lazy('home')
    template_name = 'users/delete-confirm.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['action_user'] = self.request.user
        return kwargs

    def has_permission(self):
        # also check that deleted user can_edit_profile()
        return super().has_permission() and self.can_edit_profile()

    def form_valid(self, form):
        self.object = self.get_object()
        messages.success(
            self.request,
            _("Account %(username)s was deleted successfully.") % {'username': self.object.username},
            extra_tags='modal')
        self.object.delete()
        return FormMixin.form_valid(self, form)


class TakeoutDownloadUserView(PermissionRequiredMixin, DetailView):
    permission_required = 'users.takeout'
    model = auth.get_user_model()

    def get(self, request, *args, **kwargs):
        super().get(request, *args, **kwargs)

        # TODO: Add a cache.
        takeout_tar, arcname = users.takeout.takeout(self.object)

        response = HttpResponse(takeout_tar, content_type='application/x-gzip')
        response['Content-Disposition'] = ("attachment; filename={}.tar.gz"
                                           .format(url_quote(arcname)))
        return response
