from django.contrib import admin
from gcc.models import Applicant, ApplicantLabel, Edition, Event, Corrector, SubscriberEmail, EventWish
from gcc.models import Question, Form, Answer


admin.site.register([ApplicantLabel, Edition, SubscriberEmail, Question, Form,
   EventWish])


@admin.register(Applicant)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'edition', 'status')


@admin.register(Corrector)
class CorrectorAdmin(admin.ModelAdmin):
    list_display = ('user', 'event')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('edition', 'center', 'event_start', 'event_end', 'signup_start', 'signup_end')


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('applicant', 'question', 'response')
