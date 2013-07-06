from django.db import models
from django.utils import timezone

class News(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()
    pub_date = models.DateTimeField(editable=False)
    edit_date = models.DateTimeField()

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.pub_date = timezone.now()
        self.edit_date = timezone.now()
        super(News, self).save(*args, **kwargs)
