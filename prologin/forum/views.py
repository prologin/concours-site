import datetime
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
from django.utils.functional import cached_property
from django.views.generic import ListView, RedirectView
from django.core.urlresolvers import reverse
from django.views.generic.detail import SingleObjectMixin

from guardian.mixins import PermissionRequiredMixin
from guardian.shortcuts import get_objects_for_user

import forum.models


class IndexView(ListView):
    template_name = 'forum/index.html'
    model = forum.models.Forum
    context_object_name = 'forums'

    def get_queryset(self):
        return get_objects_for_user(self.request.user, 'forum.view_forum', forum.models.Forum)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        forums = context['forums']
        context['total_thread_count'] = sum(f.thread_count for f in forums)
        context['total_post_count'] = sum(f.post_count for f in forums)
        return context


class ForumView(PermissionRequiredMixin, ListView):
    template_name = 'forum/forum_threads.html'
    model = forum.models.Thread
    context_object_name = 'threads'
    paginate_by = settings.FORUM_THREADS_PER_PAGE
    permission_required = 'forum.view_forum'

    def get_permission_object(self):
        return self.get_forum()

    def get_queryset(self):
        return super().get_queryset().select_related('author')

    def get_forum(self):
        return get_object_or_404(forum.models.Forum, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['forum'] = self.get_forum()
        # The announces will be displayed on each page of the forum
        context['announces'] = self.get_forum().threads.filter(type=forum.models.Thread.Type.announce.value)
        return context

    def get(self, request, *args, **kwargs):
        # Check if slug is valid, redirect if not
        forum = self.get_forum()
        if forum.slug != kwargs['slug']:
            return redirect('forum:forum', args=[forum.slug, forum.pk])
        return super().get(request, *args, **kwargs)


class ThreadView(PermissionRequiredMixin, ListView):
    template_name = 'forum/thread.html'
    model = forum.models.Post
    context_object_name = 'posts'
    paginate_by = settings.FORUM_POSTS_PER_PAGE
    permission_required = 'forum.view_forum'

    def get_permission_object(self):
        return self.get_thread().forum

    def get_queryset(self):
        self.thread = self.get_thread()
        return self.thread.posts.select_related('author')

    @cached_property
    def get_thread(self):
        return get_object_or_404(forum.models.Thread.objects.select_related('forum', 'author'), pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        thread = self.get_thread()
        context['thread'] = thread
        context['forum'] = thread.forum
        return context

    def get(self, request, *args, **kwargs):
        thread = self.get_thread()
        # Check if slugs are valid, redirect if not
        if thread.forum.slug != kwargs['forum_slug'] or thread.slug != kwargs['slug']:
            return redirect('forum:thread', kwargs={'forum_slug': thread.forum.slug,
                                                    'forum_pk': thread.forum.pk,
                                                    'slug': thread.slug,
                                                    'pk': thread.pk})
        return super().get(request, *args, **kwargs)


class PostRedirectView(PermissionRequiredMixin, RedirectView, SingleObjectMixin):
    permanent = False
    model = forum.models.Post
    permission_required = 'forum.view_forum'

    def get_queryset(self):
        return super().get_queryset().select_related('thread__forum')

    def get_permission_object(self):
        return self.get_object().thread.forum

    def get_redirect_url(self, *args, **kwargs):
        # Compute page number
        post = self.get_object()
        thread = post.thread
        page = (post.position // ThreadView.paginate_by) + 1
        return (reverse('forum:thread', kwargs={'forum_slug': thread.forum.slug,
                                                'forum_pk': thread.forum.pk,
                                                'slug': thread.slug,
                                                'pk': thread.pk}) + '?page={}'.format(page))
