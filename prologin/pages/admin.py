from django.contrib import admin
from pages.models import Page
from users.models import UserProfile
from prologin.utils import get_slug

class PageAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['name', 'content', 'published']}),
    ]
    list_display = ('name', 'created_by_user', 'created_on', 'edited_by_user', 'edited_on', 'published')

    def save_model(self, request, obj, form, change):
        user = UserProfile.objects.get(user__id=request.user.id)
        if not obj.created_by.id:
            obj.created_by = user
        obj.edited_by = user
        obj.slug = get_slug(obj.name)
        obj.save()

    def save_formset(self, request, form, formset, change):
        user = UserProfile.objects.get(user__id=request.user.id)
        instances = formset.save(commit=False)
        for instance in instances:
            instance.edited_by = user
            instance.save()
        formset.save_m2m()

admin.site.register(Page, PageAdmin)
