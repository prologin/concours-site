from django.contrib import admin
from gcc.models import Applicant, ApplicantLabel, Edition, Event, Trainer, SubscriberEmail
from gcc.models import Question, Answer


admin.site.register([ApplicantLabel, Edition, SubscriberEmail, Question])


@admin.register(Applicant)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'edition', 'status')


@admin.register(Trainer)
class TrainerAdmin(admin.ModelAdmin):
    list_display = ('user', 'can_view_applications')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('edition', 'center', 'event_start', 'event_end', 'signup_start', 'signup_end')


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('applicant', 'question', 'response')
