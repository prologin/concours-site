from datetime import date

from django.contrib import auth
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse,reverse_lazy

from django.views.generic import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormView, CreateView

from gcc.models import Answer, Question, Applicant, ApplicantLabel, Edition, Event, EventWish, SubscriberEmail, Forms
from sponsor.models import Sponsor
from users.models import ProloginUser

from gcc.forms import EmailForm, build_dynamic_form, ApplicationValidationForm

import users.views

import random


# Users

class LoginView(users.views.LoginView):
    template_name = 'gcc/users/login.html'


# TODO : Check that not logged in (AnonymousRequiredMixin)
class RegistrationView(users.views.RegistrationView):
    template_name = 'gcc/users/register.html'

class ProfileView(users.views.ProfileView):
    template_name = 'gcc/users/profile.html'

#FIX ME the message saying that the modifications where registered is not displaying
class EditUserView(users.views.EditUserView):
    template_name = 'gcc/users/edit.html'

    def get_success_url(self):
        return reverse('gcc:edit', args=[self.get_object().pk])

#FIX ME the message saying that the modifications where registered is not displaying
class EditPasswordView(users.views.EditPasswordView):
    template_name = 'gcc/users/edit_password.html'

    def get_success_url(self):
        return reverse('gcc:profile', args=[self.get_object().pk])

class DeleteUserView(users.views.DeleteUserView):
    template_name = 'gcc/users/delete.html'

class TakeoutDownloadUserView(users.views.TakeoutDownloadUserView):
    pass

# Editions


class EditionsView(TemplateView):
    template_name = "gcc/editions/index.html"


# About


class AboutView(TemplateView):
    template_name = "gcc/about.html"


# Homepage


class IndexView(FormView):
    template_name = "gcc/index.html"
    form_class = EmailForm
    success_url = reverse_lazy("gcc:news_confirm_subscribe")

    def form_valid(self, form):
        instance, created = SubscriberEmail.objects.get_or_create(
            email=form.cleaned_data['email'])
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['events'] = Event.objects.filter(event_end__gt = date.today())
        sponsors = list(Sponsor.active_gcc.all())
        random.shuffle(sponsors)
        context['sponsors'] = sponsors
        return context


class RessourcesView(TemplateView):
    template_name = "gcc/ressources.html"


# Newsletapplicant=None

class NewsletterUnsubscribeView(FormView):
    success_url = reverse_lazy("gcc:news_confirm_unsub")
    template_name = "gcc/news/unsubscribe.html"
    form_class = EmailForm

    def form_valid(self, form):
        try:
            account = SubscriberEmail.objects.get(
                    email=form.cleaned_data['email'])
            account.delete()
            return super().form_valid(form)
        except SubscriberEmail.DoesNotExist:
            return HttpResponseRedirect(
                    reverse_lazy("gcc:news_unsubscribe_failed"))


class NewsletterConfirmSubscribeView(TemplateView):
    template_name = "gcc/news/confirm_subscribe.html"


class NewsletterConfirmUnsubView(TemplateView):
    template_name = "gcc/news/confirm_unsub.html"


# Application

class ApplicationSummaryView(DetailView):
    model = auth.get_user_model()
    context_object_name = 'shown_user'
    template_name = 'gcc/application/summary.html'

    def get_queryset(self):
        from zinnia.models.author import Author
        self.author = Author(pk=self.kwargs[self.pk_url_kwarg])
        return super().get_queryset().prefetch_related('team_memberships')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shown_user = context[self.context_object_name]
        context['shown_author'] = self.author
        context['see_private'] = self.request.user == shown_user or self.request.user.is_staff
        context['applications'] = Applicant.objects.filter(user=self.author)
        context['current_events'] = Event.objects.filter(
            signup_start__lt = date.today(),
            signup_end__gt = date.today()
        )
        context['answers'] = [Answer.objects.filter(applicant= applic) for applic in context['applications'] ]
        return context

    def get(self, request, *args, **kwargs):
        result = super().get(request, *args, **kwargs)
        if not self.object.is_active and not self.request.user.is_staff:
            raise Http404()
        return result

class ApplicationFormView(FormView):
    template_name = 'gcc/application/form.html'

    def get_form_class(self):
        """
        Returns the form class to use in this view
        """
        return build_dynamic_form(Forms.application, self.request.user)

    def get_success_url(self):
        return reverse_lazy('gcc:application_validation')

    def form_valid(self, form):
        form.save()
        return super(FormView, self).form_valid(form)


#TODO: Check if there is an event with opened application
#TODO: Check that the user has filled ApplicationForm and isn't registered yet
class ApplicationValidation(FormView):
    template_name = 'gcc/application/validation.html'
    form_class = ApplicationValidationForm

    def get_success_url(self):
        return reverse("gcc:application_summary", kwargs={'pk': self.request.user.pk})

    def get_context_data(self, **kwargs):
        kwargs['events'] = Event.objects.filter(
            signup_start__lt = date.today(),
            signup_end__gt = date.today()
        )
        return super(ApplicationValidation, self).get_context_data(**kwargs)

    def get_initial(self):
        event_wishes = EventWish.objects.filter(applicant__user=self.request.user)
        initials = {}

        for wish in event_wishes:
            assert(wish.order in [1, 2, 3])
            field_name = 'priority' + str(wish.order)
            initials[field_name] = wish.event.pk

        return initials

    def form_valid(self, form):
        form.save(self.request.user)
        return super(ApplicationValidation, self).form_valid(form)

