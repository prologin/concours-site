from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.db import models
from django.conf import settings


class Category(models.Model):
    name = models.CharField(max_length=64, verbose_name=_('Name'))
    slug = models.SlugField(max_length=64, db_index=True)
    description = models.TextField(verbose_name=_('Description'))
    display = models.IntegerField(verbose_name=_('Display order'))
    nb_post = models.IntegerField(verbose_name=_('Number of Post'))
    nb_thread = models.IntegerField(verbose_name=_('Number of Thread'))
    last_edited_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='post_edited_by')
    last_edited_on = models.DateTimeField(auto_now=True,)
	
    def __str__(self):
        return str(_(self.name))

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')

        
class Thread(models.Model):
    name = models.CharField(max_length=64, verbose_name=_("Thread's Name"))
    slug = models.SlugField(max_length=64, db_index=True)
    category = models.ForeignKey(Category, related_name='category')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='threads_post_created_by')
    created_on = models.DateTimeField(default=timezone.now())
    last_edited_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='threads_post_edited_by')
    last_edited_on = models.DateTimeField(auto_now=True)
    pin = models.BooleanField(default=False)


class Post(models.Model):
    slug = models.SlugField(max_length=128, db_index=True)
    category = models.ForeignKey(Category, related_name='posts')
    thread = models.ForeignKey(Thread, related_name='posts')
    content = models.TextField(verbose_name=_('Content'))
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='post_created_by')
    created_on = models.DateTimeField(default=timezone.now())

    class Meta:
        verbose_name = _('Post')
        verbose_name_plural = _('Posts')
