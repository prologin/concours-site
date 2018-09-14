from django.urls import reverse_lazy
from django.http import HttpResponseRedirect

from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from gcc.models import Edition, SubscriberEmail

from gcc.forms import EmailForm

# Photos


class PhotosIndexView(TemplateView):
    template_name = "gcc/photos_index.html"


class PhotosEditionView(TemplateView):
    template_name = "gcc/photos_edition.html"


class PhotosEventView(TemplateView):
    template_name = "gcc/photos_event.html"


# Posters


class PostersView(TemplateView):
    template_name = "gcc/posters.html"


# Team


class TeamIndexView(TemplateView):
    template_name = "gcc/team_index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["editions"] = Edition.objects.order_by('-year')
        return context


class TeamEditionView(TemplateView):
    template_name = "gcc/team_edition.html"


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


# Newsletter


class NewsletterUnsubscribeView(FormView):
    success_url = reverse_lazy("gcc:news_confirm_unsub")
    template_name = "gcc/news_unsubscribe.html"
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
    template_name = "gcc/news_confirm_subscribe.html"


class NewsletterConfirmUnsubView(TemplateView):
    template_name = "gcc/news_confirm_unsub.html"
