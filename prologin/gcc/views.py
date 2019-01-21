from datetime import date

from django.contrib import auth
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy

from django.views.generic import TemplateView
from django.views.generic.edit import FormView, CreateView

from gcc.models import Answer, Applicant, ApplicantLabel, Edition, Event, EventWish, SubscriberEmail, Forms
from users.models import ProloginUser

from gcc.forms import EmailForm, build_dynamic_form, ApplicationValidationForm

import users.views


# Users

class LoginView(users.views.LoginView):
    template_name = 'gcc/users/login.html'


# TODO : Check that not logged in (AnonymousRequiredMixin)
class RegistrationView(users.views.RegistrationView):
    template_name = 'gcc/users/register.html'


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


class RessourcesView(TemplateView):
    template_name = "gcc/ressources.html"


# Newsletter


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


class ApplicationFormView(FormView):
    template_name = 'gcc/application/form.html'

    def get_form_class(self):
        """
        Returns the form class to use in this view
        """
        return build_dynamic_form(Forms.application, self.request.user)

    def get_success_url(self):
        return reverse_lazy(
            'gcc:application_validation',
            kwargs = {'user_id': self.user.pk})

    def form_valid(self, form):
        form.save()
        return super(ApplicationForm, self).form_valid(form)


#TODO: Check if there is an event with opened application
#TODO: Check that the user has filled ApplicationForm and isn't registered yet
class ApplicationValidation(FormView):
    success_url = reverse_lazy("gcc:index")
    template_name = 'gcc/application/validation.html'
    form_class = ApplicationValidationForm

    def get_context_data(self, **kwargs):
        kwargs['events'] = Event.objects.filter(
            signup_start__lt = date.today(),
            signup_end__gt = date.today()
        )
        return super(ApplicationValidation, self).get_context_data(**kwargs)

    def form_valid(self, form):
        form.save(self.request.user)
        return super(ApplicationValidation, self).form_valid(form)
