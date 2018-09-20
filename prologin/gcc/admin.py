from django.contrib import admin
from gcc.models import Edition, Event, Trainer, SubscriberEmail
from gcc.models import Question, Response


admin.site.register([Edition, SubscriberEmail, Question])

@admin.register(Trainer)
class TrainerAdmin(admin.ModelAdmin):
    list_display = ('user', 'can_view_applications')

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('edition', 'center', 'event_start', 'event_end', 'signup_start', 'signup_end')


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'response')
