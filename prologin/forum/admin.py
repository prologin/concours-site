from django.contrib import admin
from forum.models import Category, Post, Thread
from users.models import ProloginUser
from prologin.utils import get_slug

class CategoryAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['name', 'display', 'description']}),
    ]
    list_display = ('name', 'display', 'description')

    def save_model(self, request, obj, form, change):
        obj.slug = get_slug(obj.name)
        obj.save()

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            instance.slug = get_slug(instance.name)
        formset.save_m2m()

admin.site.register(Category, CategoryAdmin)



class PostAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['title', 'category', 'content']}),
    ]
    list_display = ('title', 'category', 'created_by', 'created_on')

    def save_model(self, request, obj, form, change):
        user = ProloginUser.objects.get(user__id=request.user.id)
        try:
            obj.created_by.id
        except ProloginUser.DoesNotExist:
            obj.created_by = user
        obj.edited_by = user
        obj.slug = get_slug(obj.title)
        obj.save()

    def save_formset(self, request, form, formset, change):
        user = ProloginUser.objects.get(user__id=request.user.id)
        instances = formset.save(commit=False)
        for instance in instances:
            instance.slug = get_slug(instance.title)
            instance.edited_by = user
            instance.save()
        formset.save_m2m()

admin.site.register(Post, PostAdmin)

