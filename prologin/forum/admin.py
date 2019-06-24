# Copyright (C) <2014> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

import forum.models


class ForumAdmin(admin.ModelAdmin):
    list_display = ('name', 'description',)
    search_fields = ('name', 'description',)


class ThreadAdmin(admin.ModelAdmin):
    list_display = ('title', 'first_post_author', 'forum', 'is_visible', 'is_open', 'is_sticky',)
    list_filter = ('forum', 'status', 'type', 'is_visible',)
    search_fields = ('title', 'forum__name',)
    readonly_fields = ('date_last_edited', 'last_edited_author', 'date_last_post',)
    actions = ('action_close_threads', 'action_open_threads', 'action_stick_threads', 'action_unstick_threads',)

    def action_close_threads(self, request, queryset):
        queryset.update(status=forum.models.Thread.Status.closed.value)
    action_close_threads.short_description = _("Close selected threads")

    def action_open_threads(self, request, queryset):
        queryset.update(status=forum.models.Thread.Status.normal.value)
    action_open_threads.short_description = _("Open (un-close) selected threads")

    def action_stick_threads(self, request, queryset):
        queryset.update(type=forum.models.Thread.Type.sticky.value)
    action_stick_threads.short_description = _("Make selected threads sticky")

    def action_unstick_threads(self, request, queryset):
        queryset.update(type=forum.models.Thread.Type.normal.value)
    action_unstick_threads.short_description = _("Make selected threads non-sticky")

    def is_open(self, obj):
        return not obj.is_closed
    is_open.boolean = True
    is_open.short_description = _("Is open")

    def is_sticky(self, obj):
        return obj.is_sticky
    is_sticky.boolean = True

    def first_post_author(self, thread):
        return thread.first_post.author
    first_post_author.short_description = _("Author")


class PostAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'author', 'thread', 'is_visible',)
    list_filter = ('thread__forum', 'is_visible',)
    search_fields = ('content', 'thread__title', 'thread__forum__name', 'author__username',)
    raw_id_fields = ('author', 'last_edited_author',)


admin.site.register(forum.models.Forum, ForumAdmin)
admin.site.register(forum.models.Thread, ThreadAdmin)
admin.site.register(forum.models.Post, PostAdmin)
