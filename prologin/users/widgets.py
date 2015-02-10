from django.forms.widgets import ClearableFileInput, CheckboxInput
from django.utils.html import escape, conditional_escape
from django.utils.safestring import mark_safe


class PreviewFileInput(ClearableFileInput):
    template_with_initial = '<p>%(initial_text)s<br>%(initial)s</p>%(clear_template)s<br>%(input_text)s: %(input)s'

    def render(self, name, value, attrs=None):
        substitutions = {
            'initial_text': self.initial_text,
            'input_text': self.input_text,
            'clear_template': '',
            'clear_checkbox_label': self.clear_checkbox_label,
        }
        template = '%(input)s'

        substitutions['input'] = super(ClearableFileInput, self).render(name, value, attrs)

        if value and hasattr(value, 'url'):
            template = self.template_with_initial
            attrs = self.build_attrs(attrs)
            substitutions['initial'] = '<img src="{0}" {1}/>'.format(
                escape(value.url),
                " ".join('%s="%s"' % (escape(k), escape(v)) for k, v in attrs.items()) if attrs else "",
            )
            if not self.is_required:
                checkbox_name = self.clear_checkbox_name(name)
                checkbox_id = self.clear_checkbox_id(checkbox_name)
                substitutions['clear_checkbox_name'] = conditional_escape(checkbox_name)
                substitutions['clear_checkbox_id'] = conditional_escape(checkbox_id)
                substitutions['clear'] = CheckboxInput().render(checkbox_name, False, attrs={'id': checkbox_id})
                substitutions['clear_template'] = self.template_with_clear % substitutions

        return mark_safe(template % substitutions)
