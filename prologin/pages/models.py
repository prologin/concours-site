from django.db import models
from users.models import UserProfile
from menu.models import MenuEntry

class Page(models.Model):
    name = models.CharField(max_length=128)
    slug = models.SlugField(max_length=128, db_index=True)
    content = models.TextField()
    container = models.ForeignKey(MenuEntry, blank=True, null=True, on_delete=models.SET_NULL, limit_choices_to={'parent': None})
    created_by = models.ForeignKey(UserProfile, related_name='page_created_by')
    created_on = models.DateTimeField(auto_now_add=True)
    edited_by = models.ForeignKey(UserProfile, related_name='page_edited_by')
    edited_on = models.DateTimeField(auto_now=True)
    published = models.BooleanField(default=None)

    def created_by_user(self):
        return self.created_by.user.username

    def edited_by_user(self):
        return self.edited_by.user.username
