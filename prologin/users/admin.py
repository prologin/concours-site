from users.models import User
from django.contrib import admin

class UserAdmin(admin.ModelAdmin):
	list_display = ('prenom', 'nom')

admin.site.register(User, UserAdmin)
