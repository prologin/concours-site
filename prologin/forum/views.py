from django.conf import settings
from django.contrib import messages
from django.urls import reverse
from django.db import transaction
from django.db.models import Q
from django.http.response import HttpResponseForbidden, JsonResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView, RedirectView, CreateView, UpdateView, DeleteView, View
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import ModelFormMixin, FormMixin
from rules.contrib.views import PermissionRequiredMixin

import forum.forms
import forum.models

class PreviewMixin:
    preview_name = 'preview'

    def has_preview(self, request):
        return bool(request.POST.get(self.preview_name))

    def post(self, request, *args, **kwargs):
        if self.has_preview(request):
            return self.get(request, *args, **kwargs)
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['preview'] = bool(self.has_preview(self.request))
        return context


def cite_post_content(post):
    # Python module 'textwrap' behaves strangely, dropping previous indents or randomly dropping whitespaces
    # even if you disable that. If you can make it work, feel free to replace the lines below.
    content = post.content
    content = '\n'.join('> {}'.format(line) for line in content.split('\n'))
    return "**{}**\n{}\n\n".format(post.author.username, content)


class IndexView(ListView):
    template_name = 'forum/index.html'
    model = forum.models.Forum
    context_object_name = 'forums'

    def get_queryset(self):
        return list(filter(lambda f: self.request.user.has_perm('forum.view_forum', f), super().get_queryset()))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        forums = context['forums']
        context['total_thread_count'] = sum(f.thread_count for f in forums)
        context['total_post_count'] = sum(f.post_count for f in forums)
        return context


class ForumView(PermissionRequiredMixin, ListView):
    # TODO: check perms for view
    template_name = 'forum/forum_threads.html'
    model = forum.models.Thread
    context_object_name = 'threads'
    paginate_by = settings.FORUM_THREADS_PER_PAGE
    permission_required = 'forum.view_forum'

    @cached_property
    def get_forum(self):
        return get_object_or_404(forum.models.Forum, pk=self.kwargs['pk'])

    def get_permission_object(self):
        return self.get_forum

    def get_queryset(self):
        return (self.model.objects
                .with_readstate_of(self.request.user)
                .select_related('forum')
                .filter(forum=self.get_forum))

    def paginate_queryset(self, queryset, page_size):
        paginator, page, page.object_list, page.has_other_pages = super().paginate_queryset(queryset, page_size)
        first_post_ids = set()
        last_post_ids = set()
        for thread in page.object_list:
            assert thread.first_post_id is not None
            assert thread.last_post_id is not None
            first_post_ids.add(thread.first_post_id)
            last_post_ids.add(thread.last_post_id)

        # Map threads to their first and last post
        # If we don't include 'thread' in select_related, Django is stupid enough to trigger a new query for thread.pk
        # even though it is available as thread_id.
        thread_to_posts = {}
        for post in forum.models.Post.objects.filter(pk__in=first_post_ids).select_related('author', 'thread'):
            thread_to_posts[post.thread.pk] = [post, None]
        for post in forum.models.Post.objects.filter(pk__in=last_post_ids).select_related('author', 'thread'):
            thread_to_posts[post.thread.pk][1] = post

        # Hydrate the threads
        for thread in page.object_list:
            thread._first_post, thread._last_post = thread_to_posts[thread.pk]

        return paginator, page, page.object_list, page.has_other_pages

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['forum'] = self.get_forum
        # The announces will be displayed on each page of the forum
        threads = context['threads']
        context['sticky_threads'] = [thread for thread in threads if thread.is_sticky]
        context['normal_threads'] = threads[len(context['sticky_threads']):]
        context['announces'] = self.get_forum.threads.filter(type=forum.models.Thread.Type.announce.value)
        return context

    def get(self, request, *args, **kwargs):
        # Check if slug is valid, redirect if not
        forum = self.get_forum
        if forum.slug != kwargs['slug']:
            return redirect('forum:forum', slug=forum.slug, pk=forum.pk)
        return super().get(request, *args, **kwargs)


class CreateThreadView(PermissionRequiredMixin, PreviewMixin, CreateView):
    # TODO: permission checking
    template_name = 'forum/create_thread.html'
    model = forum.models.Thread
    form_class = forum.forms.ThreadForm
    permission_required = 'forum.create_thread'

    @cached_property
    def get_forum(self):
        return get_object_or_404(forum.models.Forum, pk=self.kwargs['forum_pk'])

    def get_permission_object(self):
        return self.get_forum

    def get_success_url(self):
        # Django tries to do smart shit
        return self.success_url

    def form_valid(self, form):
        thread = form.save(commit=False)
        thread.forum = self.get_forum
        with transaction.atomic():
            thread.save()
            first_post = forum.models.Post(author=self.request.user, content=form.cleaned_data['content'], thread=thread)
            first_post.save()  # will trigger thread update
        self.success_url = first_post.get_absolute_url()
        return super(ModelFormMixin, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['forum'] = self.get_forum
        return context


class ThreadView(PermissionRequiredMixin, PreviewMixin, FormMixin, ListView):
    # TODO: check perms for view AND post (ie. new post in thread)
    template_name = 'forum/thread_posts.html'
    model = forum.models.Post
    form_class = forum.forms.PostForm
    context_object_name = 'posts'
    paginate_by = settings.FORUM_POSTS_PER_PAGE
    permission_required = 'forum.view_thread'

    @cached_property
    def get_thread(self):
        return get_object_or_404(forum.models.Thread.objects.select_related('forum'), pk=self.kwargs['pk'])

    def get_permission_object(self):
        return self.get_thread

    def get_queryset(self):
        self.thread = self.get_thread
        return self.thread.posts.select_related('author')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        thread = self.get_thread
        context['thread'] = thread
        context['forum'] = thread.forum
        context['form'] = kwargs.get('form', self.get_form())
        if self.request.user.has_perm('forum.edit_thread_lock'):
            status = (forum.models.Thread.Status.normal if thread.is_closed else forum.models.Thread.Status.closed).value
            context['edit_thread_lock_form'] = forum.forms.EditThreadLockForm(instance=thread, initial={'status': status})
        if self.request.user.has_perm('forum.edit_thread_pin'):
            type = (forum.models.Thread.Type.normal if thread.is_sticky else forum.models.Thread.Type.sticky).value
            context['edit_thread_pin_form'] = forum.forms.EditThreadPinForm(instance=thread, initial={'type': type})
        if self.request.user.has_perm('forum.move_thread'):
            context['move_thread_form'] = forum.forms.MoveThreadForm(instance=thread)
        cite_post_id = self.request.GET.get('cite')
        if cite_post_id:
            post = get_object_or_404(self.model, pk=cite_post_id)
            if self.request.user.has_perm('forum.view_post', post):
                raise Http404()
            context['form'].initial['content'] = cite_post_content(post)

        # If user is logged and on the last page of the thread, mark the
        # thread as read.
        # XXX: This shouldn't be in get_context_data() but in get(), but we
        # can't access the paginated posts in get() without reexecuting the
        # query by calling paginate_queryset().
        if ((self.request.user.is_authenticated
             and not context['page_obj'].has_next())):
            robj = thread.mark_read_by(self.request.user)
            context["subscribed"] = (robj.subtype == forum.models.ReadState.SubscribeType.notification.value)

        return context

    def get(self, request, *args, **kwargs):
        thread = self.get_thread
        # Check if slugs are valid, redirect if not
        if thread.forum.slug != kwargs['forum_slug'] or thread.slug != kwargs['slug']:
            return redirect('forum:thread',
                            forum_slug=thread.forum.slug,
                            forum_pk=thread.forum.pk,
                            slug=thread.slug,
                            pk=thread.pk)
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        post = form.save(commit=False)
        post.author = self.request.user
        post.thread = self.get_thread
        post.save()

        ## Notification Subsystem
        notify_post_on_thread_subscribed(self.get_thread, post)

        self.success_url = post.get_absolute_url()
        return super().form_valid(form)

    def post(self, request, *args, **kwargs):
        if not self.request.user.has_perm('forum.create_post', self.get_thread):
            return HttpResponseForbidden()

        form = self.get_form()
        if form.is_valid() and not self.has_preview(request):
            return self.form_valid(form)
        else:
            return self.get(request, *args, **kwargs)


class EditPostView(PermissionRequiredMixin, PreviewMixin, UpdateView):
    template_name = 'forum/edit_post.html'
    model = forum.models.Post
    permission_required = 'forum.edit_post'

    def get_queryset(self):
        return super().get_queryset().select_related('thread', 'thread__forum')

    @cached_property
    def get_thread(self):
        return self.get_object().thread

    def get_form_class(self):
        if self.request.user.is_staff:
            return forum.forms.StaffUpdatePostForm
        return forum.forms.UpdatePostForm

    def form_valid(self, form):
        post = form.save(commit=False)
        post.last_edited_author = self.request.user
        post.save()
        if post.is_thread_head:
            post.thread.title = form.cleaned_data['thread_title']
            post.thread.save()
        return super(ModelFormMixin, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['thread'] = self.get_thread
        context['forum'] = self.get_thread.forum
        return context


class PostRedirectView(PermissionRequiredMixin, RedirectView, SingleObjectMixin):
    permanent = False
    model = forum.models.Post
    permission_required = 'forum.view_post'

    def get_queryset(self):
        return super().get_queryset().select_related('thread__forum')

    def get_redirect_url(self, *args, **kwargs):
        # Compute page number
        post = self.get_object()
        thread = post.thread
        page = (post.position - 1) // ThreadView.paginate_by + 1
        return (reverse('forum:thread', kwargs={'forum_slug': thread.forum.slug,
                                                'forum_pk': thread.forum.pk,
                                                'slug': thread.slug,
                                                'pk': thread.pk}) + '?page={}#message-{}'.format(page, post.pk))


class EditPostVisibilityView(PermissionRequiredMixin, UpdateView):
    model = forum.models.Post
    fields = ('is_visible',)
    permission_required = 'forum.edit_post_visibility'


class DeletePostView(PermissionRequiredMixin, DeleteView):
    model = forum.models.Post
    permission_required = 'forum.delete_post'
    context_object_name = 'post'

    def get_success_url(self):
        # it's the thread head, so when deleted, we redirect to the forum URL
        if self.object.is_thread_head:
            return self.object.thread.forum.get_absolute_url()
        return self.object.thread.get_absolute_url()

    def delete(self, request, *args, **kwargs):
        messages.success(request, _("The post was deleted successfully."))
        return super().delete(request, *args, **kwargs)


class CitePostView(PermissionRequiredMixin, SingleObjectMixin, RedirectView):
    permanent = False
    model = forum.models.Post
    permission_required = 'forum.create_post'

    def get_permission_object(self):
        return self.get_object().thread

    def get_redirect_url(self, *args, **kwargs):
        post = self.get_object()
        thread = post.thread
        kwargs = {'forum_slug': thread.forum.slug,
                  'forum_pk': thread.forum.pk,
                  'slug': thread.slug,
                  'pk': thread.pk}
        url = reverse('forum:thread', kwargs=kwargs)
        return '{}?cite={}#id_content'.format(url, post.pk)

    def get_object(self, queryset=None):
        post = super().get_object(queryset)
        if not self.request.user.has_perm('forum.view_post', post):
            raise Http404()
        return post

    def get(self, request, *args, **kwargs):
        # Ajax request
        if 'application/json' in request.META.get('HTTP_ACCEPT', ''):
            return JsonResponse({'message': cite_post_content(self.get_object())})
        # Standard request
        return super().get(request, *args, **kwargs)


class EditThreadLockView(PermissionRequiredMixin, UpdateView):
    model = forum.models.Thread
    form_class = forum.forms.EditThreadLockForm
    permission_required = 'forum.edit_thread_lock'


class EditThreadPinView(PermissionRequiredMixin, UpdateView):
    model = forum.models.Thread
    form_class = forum.forms.EditThreadPinForm
    permission_required = 'forum.edit_thread_pin'


class MoveThreadView(PermissionRequiredMixin, UpdateView):
    model = forum.models.Thread
    form_class = forum.forms.MoveThreadForm
    permission_required = 'forum.move_thread'

    def form_valid(self, form):
        messages.success(self.request, _("The thread was moved successfully."))
        return super().form_valid(form)


class DeleteThreadView(PermissionRequiredMixin, DeleteView):
    model = forum.models.Thread
    permission_required = 'forum.delete_thread'
    context_object_name = 'thread'

    def get_success_url(self):
        return self.object.forum.get_absolute_url()

    def delete(self, request, *args, **kwargs):
        messages.success(request, _("The thread was deleted successfully."))
        return super().delete(request, *args, **kwargs)

class SubscribeThreadView(PermissionRequiredMixin, View):
    model = forum.models.Thread
    permission_required = 'forum.view_thread'
    context_object_name = 'thread'

    def get_success_url(self):
        return reverse("forum:thread", kwargs=self.kwargs)

    def post(self, request, *args, **kwargs):
        thread = get_object_or_404(forum.models.Thread, slug=self.kwargs['slug'], pk=self.kwargs['pk'])
        rs = get_object_or_404(forum.models.ReadState, user=request.user, thread=thread)
        if rs.subtype == forum.models.ReadState.SubscribeType.nothing.value:
            rs.subtype = forum.models.ReadState.SubscribeType.notification.value
            messages.success(request, _("You subscribed to the thread successfully."))
        else:
            rs.subtype = forum.models.ReadState.SubscribeType.nothing.value
            if rs.notification != None:
                rs.notification.new_post_count = 0
                rs.notification.save()
            messages.success(request, _("You unsubscribed to the thread successfully."))
        rs.save()
        return redirect(self.get_success_url())
    
    def get(self, request, *args, **kwargs):
        if request.method == "POST":
            return self.post(request, *args, **kwargs)
        raise Http404()


class NotificationView(PermissionRequiredMixin, ListView):
    template_name = 'forum/notification.html'
    permission_required = 'forum.view_thread'
    
    def get_queryset(self):
        return forum.models.Notification.objects.filter(user=self.request.user).filter(~Q(new_post_count=0))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["notifications"] = self.get_queryset()

        return context

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/')
        return super().get(request, *args, **kwargs)

def notify_post_on_thread_subscribed(thread, post):

    rs_query = forum.models.ReadState.objects.filter(thread=thread, subtype=1)

    for rs in rs_query:
        rs.notification.last_post = post
        rs.notification.last_author = post.author
        rs.notification.new_post_count += 1
        rs.notification.save()
    
    return rs_query
