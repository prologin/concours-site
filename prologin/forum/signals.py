from django.db.models.signals import post_delete
from django.dispatch import receiver
from forum.models import Post,Thread


@receiver(post_delete, sender=Post)
def update_thread_on_post_deletion(sender, instance, using, **kwargs):
    # post was deleted, so checking instance.is_thread_head won't work
    try:
        if (not Post.objects.filter(thread=instance.thread).exists() or
                instance.date_created < instance.thread.first_post.date_created):
            instance.thread.delete()
        else:
            instance.thread.update_trackers()
    except Thread.DoesNotExist:
        pass
