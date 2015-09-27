from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.db import models
from users.models import ProloginUser


class Category(models.Model):
    name = models.CharField(max_length=64, verbose_name=_('Name'))
    slug = models.SlugField(max_length=64, db_index=True)
    description = models.TextField(verbose_name=_('Description'))
    display = models.IntegerField(verbose_name=_('Display order'))

    def __str__(self):
        return str(_(self.name))

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
        
class Thread(models.Model):
    name = models.CharField(max_length=64, verbose_name=_("Thread's Name"))
    slug = models.SlugField(max_length=64, db_index=True)
    category = models.ForeignKey(Category, related_name='T_category')
    created_by = models.ForeignKey(ProloginUser, related_name='T_post_created_by')
    created_on = models.DateTimeField()
    last_edited_by = models.ForeignKey(ProloginUser, related_name='T_post_edited_by')
    last_edited_on = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.id:
            self.created_on = timezone.now()
        return super(Thread, self).save(*args, **kwargs)

class Post(models.Model):
    title = models.CharField(max_length=200, verbose_name=_('Title'))
    slug = models.SlugField(max_length=128, db_index=True)
    category = models.ForeignKey(Category, related_name='category')
    thread = models.ForeignKey(Thread, related_name='thread')
    content = models.TextField(verbose_name=_('Content'))
    created_by = models.ForeignKey(ProloginUser, related_name='post_created_by')
    created_on = models.DateTimeField()


    class Meta:
        verbose_name = _('Post')
        verbose_name_plural = _('Posts')

    def save(self, *args, **kwargs):
        if not self.id:
            self.created_on = timezone.now()
        return super(Post, self).save(*args, **kwargs)