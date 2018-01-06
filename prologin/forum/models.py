from adminsortable.models import SortableMixin
from django.conf import settings
from django.urls import reverse
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.encoding import force_text
from django.utils.functional import cached_property
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _, ugettext_noop
from django_prometheus.models import ExportModelOperationsMixin

from prologin.models import EnumField
from prologin.utils import ChoiceEnum

from forum import managers


class Forum(ExportModelOperationsMixin('forum'), SortableMixin):
    name = models.CharField(max_length=255, verbose_name=_("Name"))
    slug = models.SlugField(max_length=300, db_index=True)
    description = models.TextField(verbose_name=_("Description"))
    order = models.IntegerField(editable=False, db_index=True)

    thread_count = models.PositiveIntegerField(verbose_name=_("Number of threads"), editable=False, blank=True, default=0)
    post_count = models.PositiveIntegerField(verbose_name=_("Number of posts"), editable=False, blank=True, default=0)

    class Meta:
        ordering = ('order',)
        verbose_name = _("Forum")
        verbose_name_plural = _("Forums")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(force_text(self.name))
        super().save(*args, **kwargs)

    @cached_property
    def last_post(self):
        return Post.visible.filter(thread__forum=self).latest()

    def update_trackers(self):
        visible_threads = Thread.objects.filter(is_visible=True, forum=self).order_by('-date_last_post')

        self.thread_count = visible_threads.count()
        self.post_count = Post.objects.filter(is_visible=True, thread__forum=self, thread__is_visible=True).count()

        try:
            self.date_last_post = visible_threads[0].date_last_post
        except IndexError:
            self.date_last_post = timezone.now()

        super().save()

    def get_absolute_url(self):
        return reverse('forum:forum', kwargs={'slug': self.slug, 'pk': self.pk})


class Thread(ExportModelOperationsMixin('thread'), models.Model):
    @ChoiceEnum.labels(str.capitalize)
    class Type(ChoiceEnum):
        normal = 0
        sticky = 1
        announce = 2
        ugettext_noop("Normal")
        ugettext_noop("Sticky")
        ugettext_noop("Announce")

    @ChoiceEnum.labels(str.capitalize)
    class Status(ChoiceEnum):
        normal = 0
        closed = 1
        moved = 2
        ugettext_noop("Normal")
        ugettext_noop("Closed")
        ugettext_noop("Moved")

    forum = models.ForeignKey(Forum, related_name='threads', on_delete=models.CASCADE)

    title = models.CharField(max_length=255, verbose_name=_("Title"))
    slug = models.SlugField(max_length=300, db_index=True)

    type = EnumField(Type, db_index=True, verbose_name=_("Thread type"), default=Type.normal.value)
    status = EnumField(Status, db_index=True, verbose_name=_("Thread status"), default=Status.normal.value)
    is_visible = models.BooleanField(default=True, db_index=True, verbose_name=_("Visible"))

    date_last_edited = models.DateTimeField(auto_now=True)
    last_edited_author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='forum_last_edited_threads',
                                           blank=True, null=True, on_delete=models.SET_NULL)

    post_count = models.PositiveIntegerField(verbose_name=_("Number of posts"), editable=False, blank=True, default=0)
    date_last_post = models.DateTimeField(verbose_name=_("Last post added on"), blank=True, null=True)  # so we can sort

    # Managers
    objects = models.Manager()
    visible = managers.VisibleObjectsManager()

    class Meta:
        ordering = ('-type', '-date_last_post')
        get_latest_by = 'date_last_post'
        verbose_name = _("Thread")
        verbose_name_plural = _("Threads")

    def __str__(self):
        return self.title

    @cached_property
    def is_moved(self):
        return self.status == Thread.Status.moved.value

    @cached_property
    def is_closed(self):
        return self.status == Thread.Status.closed.value

    @cached_property
    def is_open(self):
        return not self.is_closed

    @cached_property
    def is_standard(self):
        return self.type == Thread.Type.normal.value

    @cached_property
    def is_sticky(self):
        return self.type == Thread.Type.sticky.value

    @cached_property
    def is_announce(self):
        return self.type == Thread.Type.announce.value

    @cached_property
    def date_created(self):
        return self.first_post.date_created

    @cached_property
    def author(self):
        return self.first_post.author

    @cached_property
    def first_post(self):
        # Try an externally hydrated first_post first
        if hasattr(self, '_first_post'):
            return self._first_post
        posts = self.posts.select_related('author').order_by('date_created')
        try:
            return posts[0]
        except IndexError:
            return None

    @cached_property
    def last_post(self):
        # Try an externally hydrated last_post first
        if hasattr(self, '_last_post'):
            return self._last_post
        posts = self.posts.select_related('author').order_by('-date_created')
        try:
            return posts[0]
        except IndexError:
            return None

    def save(self, *args, **kwargs):
        # Keep track of old instance so we can update the forum trackers of the old forum to which this belongs
        old_instance = None
        if self.pk:
            old_instance = self.__class__._default_manager.get(pk=self.pk)

        self.slug = slugify(force_text(self.title))
        super().save(*args, **kwargs)

        # If any change has been made to the parent forum, trigger the update of the counters
        if old_instance and old_instance.forum != self.forum:
            old_instance.forum.update_trackers()
            self.update_trackers()

    def update_trackers(self):
        posts = Post.objects.filter(thread=self)
        self.post_count = posts.count()
        self.date_last_post = posts.latest().date_created
        super().save()
        self.forum.update_trackers()

    def delete(self, using=None):
        super().delete(using)
        self.forum.update_trackers()

    def get_absolute_url(self):
        return reverse('forum:thread', kwargs={'forum_slug': self.forum.slug,
                                               'forum_pk': self.forum.pk,
                                               'slug': self.slug,
                                               'pk': self.pk})


class Post(ExportModelOperationsMixin('post'), models.Model):
    thread = models.ForeignKey(Thread, related_name='posts', on_delete=models.CASCADE)

    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='forum_posts', on_delete=models.CASCADE)
    content = models.TextField(verbose_name=_("Content"))

    date_created = models.DateTimeField(default=timezone.now)
    date_last_edited = models.DateTimeField(auto_now=True)
    last_edited_author = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True,
                                           related_name='forum_last_edited_posts', on_delete=models.SET_NULL)
    last_edited_reason = models.TextField(verbose_name=_("Edit reason"), blank=True)

    is_visible = models.BooleanField(default=True, db_index=True)

    # Managers
    objects = models.Manager()
    visible = managers.VisibleObjectsManager()

    class Meta:
        ordering = ('date_created',)
        get_latest_by = 'date_created'
        verbose_name = _("Post")
        verbose_name_plural = _("Posts")

    def __str__(self):
        return self.content[:64] + ('…' if len(self.content) > 64 else '')

    @cached_property
    def is_edited(self):
        return self.last_edited_author is not None

    @cached_property
    def is_thread_head(self):
        """
        Returns True if the post is the first post of the thread.
        """
        return self.thread.first_post.id == self.id

    @cached_property
    def is_thread_tail(self):
        """
        Returns True if the post is the last post of the thread.
        """
        return self.thread.last_post.id == self.id

    @cached_property
    def position(self):
        """
        Returns an integer corresponding to the position of the post in the thread.
        """
        return self.thread.posts.filter(Q(date_created__lt=self.date_created) | Q(pk=self.pk)).distinct().count()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_thread_head:
            if self.is_visible != self.thread.is_visible:
                self.thread.is_visible = self.is_visible
        # Trigger the thread-level trackers update
        self.thread.update_trackers()

    def delete(self, using=None):
        if self.is_thread_head:
            self.thread.delete()
        else:
            super().delete(using)
            self.thread.update_trackers()

    def get_absolute_url(self):
        thread = self.thread
        page = (self.position - 1) // settings.FORUM_POSTS_PER_PAGE + 1
        return (reverse('forum:thread', kwargs={'forum_slug': thread.forum.slug,
                                                'forum_pk': thread.forum.pk,
                                                'slug': thread.slug,
                                                'pk': thread.pk}) + '?page={}#message-{}'.format(page, self.pk))

    def get_permalink(self):
        return reverse('forum:post', kwargs={'thread_slug': self.thread.slug, 'pk': self.pk})


@receiver(post_save, sender=Post)
def thread_save_handler(sender, **kwargs):
    post = kwargs.get('instance')
    if not post or not kwargs.get('created') or not post.is_thread_head:
        return
    # args need to be serializable
    data = {
        'username': post.author.username,
        'forum': post.thread.forum.name,
        'title': post.thread.title,
        'url': '{}{}'.format(settings.SITE_BASE_URL, post.get_permalink()),
    }
    from forum.tasks import notify_new_thread
    try:
        notify_new_thread.apply_async(args=[data])
    except Exception:
        pass
