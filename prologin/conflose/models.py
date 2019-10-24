from django.db import models
from django.contrib.auth import get_user_model


class Conflose(models.Model):
    name = models.CharField(max_length=30)
    css = models.TextField()

    def __str__(self):
        return self.name


class UserConflose(models.Model):
    user = models.OneToOneField(get_user_model(), related_name='userconflose',
                                on_delete=models.CASCADE)
    conflose = models.ForeignKey(Conflose, related_name='userconfloses',
                                 on_delete=models.CASCADE)
    message = models.TextField(blank=True)
