from django import forms
from forum.models import Post, Thread


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content']


class ThreadFromStaff(forms.ModelForm):
    class Meta:
        model = Thread
        fields = ['name', 'pin']


class ThreadFrom(forms.ModelForm):
    class Meta:
        model = Thread
        fields = ['name']