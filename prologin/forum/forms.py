from django import forms
from django.utils.translation import ugettext_lazy as _

from forum.models import Post, Thread


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('content',)
        labels = {
            'content': '',
        }
        widgets = {
            'content': forms.Textarea(attrs={
                'placeholder': _("Compose your message here. You can use the Markdown syntax."),
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

    def clean_last_edited_reason(self):
        return self.cleaned_data['last_edited_reason'].strip()


class StaffUpdatePostForm(UpdatePostForm):
    class Meta(UpdatePostForm.Meta):
        fields = UpdatePostForm.Meta.fields + ('is_visible',)
        labels = dict({'is_visible': _("Post is visible")}, **UpdatePostForm.Meta.labels)


class ThreadForm(forms.ModelForm):
    content = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Thread
        fields = ('title',)
