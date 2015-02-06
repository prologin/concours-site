from django.contrib import admin
from zinnia.models.entry import Entry
from zinnia.admin.entry import EntryAdmin


admin.site.register(Entry, EntryAdmin)
