from django.contrib import admin

import forum.models


class ForumAdmin(admin.ModelAdmin):
    list_display = ('name', 'description',)
    readonly_fields = ('date_last_post',)


class ThreadAdmin(admin.ModelAdmin):
    raw_id_fields = ('author', )
    readonly_fields = ('date_last_edited', 'last_edited_author', 'date_last_post',)


class PostAdmin(admin.ModelAdmin):
    raw_id_fields = ('author',)


admin.site.register(forum.models.Forum, ForumAdmin)
admin.site.register(forum.models.Thread, ThreadAdmin)
admin.site.register(forum.models.Post, PostAdmin)
