import collections
import itertools

from django import forms
from django.utils.translation import ugettext_lazy as _

from forum.models import Post, Thread

MESSAGE_CONTENT_PLACEHOLDER = _("Compose your message here. You can use the Markdown syntax.")


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('content',)
        labels = {
            'content': '',
        }
        widgets = {
            'content': forms.Textarea(attrs={
                'placeholder': MESSAGE_CONTENT_PLACEHOLDER,
                'rows': 4}),
        }

    def clean_content(self):
        return self.cleaned_data['content'].strip()


class UpdatePostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = PostForm.Meta.fields + ('last_edited_reason',)
        labels = {
            'content': '',
            'last_edited_reason': _("Optional explanation"),
        }
        widgets = {
            'last_edited_reason': forms.TextInput(attrs={
                'placeholder': _("This explanation will be shown above the message.")})
        }

    @property
    def is_thread_head(self):
        return self.instance and self.instance.is_thread_head

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.is_thread_head:
            # Add thread title
            # Django forms are shit, so we have to rebuild the damn OrderedDict from scratch
            self.fields = collections.OrderedDict(field for field in itertools.chain(
                [('thread_title', forms.CharField(label=_("Thread title")))],
                self.fields.items()
            ))
            self.initial['thread_title'] = self.instance.thread.title

    def clean_last_edited_reason(self):
        return self.cleaned_data['last_edited_reason'].strip()


class StaffUpdatePostForm(UpdatePostForm):
    class Meta(UpdatePostForm.Meta):
        fields = UpdatePostForm.Meta.fields + ('is_visible',)
        labels = dict({'is_visible': _("Post is visible")}, **UpdatePostForm.Meta.labels)


class ThreadForm(forms.ModelForm):
    content = forms.CharField(min_length=1, required=True,
                              widget=forms.Textarea(attrs={'placeholder': MESSAGE_CONTENT_PLACEHOLDER}),
                              label=_("Message content"))

    class Meta:
        model = Thread
        fields = ('title', 'content')
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': _("Choose a short, descriptive title.")})
        }

    def clean_title(self):
        return self.cleaned_data['title'].strip()

    def clean_content(self):
        return self.cleaned_data['content'].strip()
