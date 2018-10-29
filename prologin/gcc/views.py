from datetime import date

from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy

from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from gcc.models import Answer, Applicant, ApplicantLabel, Edition, Event, EventWish, SubscriberEmail, Trainer, Forms
from users.models import ProloginUser

from gcc.forms import EmailForm, build_dynamic_form, ApplicationValidationForm

# Photos


class PhotosIndexView(TemplateView):
    template_name = "gcc/photos_index.html"

class PhotosEditionView(TemplateView):
    template_name = "gcc/photos_edition.html"


class PhotosEventView(TemplateView):
    template_name = "gcc/photos_event.html"


# Posters


class EditionsView(TemplateView):
    template_name = "gcc/editions.html"


# Team


class TeamIndexView(TemplateView):
    template_name = "gcc/team/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["editions"] = Edition.objects.order_by('-year')
        context["trainers"] = Trainer.objects.order_by('user__last_name', 'user__first_name')
        return context


class TeamEditionView(TemplateView):
    template_name = "gcc/team/edition.html"

    def get_context_data(self, year):
        context = {
            'edition': get_object_or_404(Edition, year=year)
        }
        return context


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


class SponsorsView(TemplateView):
    template_name = "gcc/sponsors.html"


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


#TODO: Check if the user is logged in
class ApplicationForm(FormView):
    template_name = 'gcc/application/form.html'

    def get_form_class(self):
        """
        Returns the form class to use in this view
        """
        self.user = get_object_or_404(ProloginUser, pk=self.kwargs['user_id'])
        return build_dynamic_form(Forms.application, self.user)

    def get_success_url(self):
        return reverse_lazy(
            'gcc:application_validation',
            kwargs = {'user_id': self.user.pk})

    def form_valid(self, form):
        form.save()
        return super(ApplicationForm, self).form_valid(form)


#TODO: Check if the user is logged in
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
        self.user = get_object_or_404(ProloginUser, pk=self.kwargs['user_id'])
        form.save(self.user)
        return super(ApplicationValidation, self).form_valid(form)


# Application moderation


#TODO: Check permissions to access this page
class ApplicationIndexView(TemplateView):
    template_name = "gcc/application/index.html"

    def get_context_data(self, **kwargs):
        """
        Extract the list of users who have an application this year and list
        their applications in the same object.
        """
        #TODO: permissions to moderate each event ?
        current_edition = Edition.objects.latest('year')

        context = {
            'applicants': Applicant.objects.filter(edition=current_edition),
            'labels': ApplicantLabel.objects.all(),
        }

        return context


# TODO: Check permissions
def application_remove_label(request, applicant_id, label_id):
    applicant = get_object_or_404(Applicant, pk=applicant_id)
    label = get_object_or_404(ApplicantLabel, pk=label_id)
    applicant.labels.remove(label)
    return redirect(
        reverse_lazy('gcc:application_index') + '#applicant-{}'.format(applicant.pk))

# TODO: Check permissions
def application_add_label(request, applicant_id, label_id):
    applicant = get_object_or_404(Applicant, pk=applicant_id)
    label = get_object_or_404(ApplicantLabel, pk=label_id)
    applicant.labels.add(label)
    return redirect(
        reverse_lazy('gcc:application_index') + '#applicant-{}'.format(applicant.pk))
