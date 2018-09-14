from django.contrib import admin
from gcc.models import Edition, Event, Trainer, SubscriberEmail

admin.site.register([Edition, Event, Trainer, SubscriberEmail])
