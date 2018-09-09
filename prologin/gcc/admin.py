from django.contrib import admin
from gcc.models import Edition, Event, Trainer

admin.site.register([Edition, Event, Trainer])
