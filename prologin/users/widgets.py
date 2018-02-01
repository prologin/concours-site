from django.forms.widgets import ClearableFileInput
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _


class PreviewFileInput(ClearableFileInput):
    input_text = _("Upload new image")
    template_name = 'users/peview-file-input.html'

    def __init__(self, *args, **kwargs):
        self.image_attrs = kwargs.pop('image_attrs', {})
        super().__init__(*args, **kwargs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['image_attrs'] = (
            mark_safe(" ".join(format_html('{}="{}"', k, v) for k, v in self.image_attrs.items())
            if self.image_attrs else ""))
        return context
