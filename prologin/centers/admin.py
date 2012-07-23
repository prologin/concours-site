from centers.models import Center
from django.contrib import admin

class CenterAdmin(admin.ModelAdmin):
	list_display = ('nom', 'ville')

admin.site.register(Center, CenterAdmin)