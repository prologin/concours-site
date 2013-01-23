from users.models import UserProfile
from django.contrib import admin

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'address', 'postal_code', 'city', 'newsletter')

admin.site.register(UserProfile, UserProfileAdmin)
