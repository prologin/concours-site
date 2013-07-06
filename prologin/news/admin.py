from django.contrib import admin
from news.models import News

class NewsAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,               {'fields': ['title', 'body']}),
    ]
    list_display = ('title', 'pub_date', 'edit_date')

admin.site.register(News, NewsAdmin)
