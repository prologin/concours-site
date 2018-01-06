import time
from django.forms.widgets import ClearableFileInput, CheckboxInput
from django.utils.html import conditional_escape, format_html
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _


class PreviewFileInput(ClearableFileInput):
    input_text = _("Upload new image")
    template_empty = """
    <div class="panel panel-default panel-form"><div class="panel-body">
    <div class="row">
        <div class="col-xs-3" style="text-align: center;">
            <i class="fa fa-image fa-2x text-muted"></i>
        </div>
        <div class="col-xs-9">
            <p>%(input)s</p>
        </div>
    </div></div></div>
    """
    template_with_initial = """
    <div class="panel panel-default panel-form"><div class="panel-body">
    <div class="row">
        <div class="col-xs-3" style="text-align: center;">
            %(initial)s
        </div>
        <div class="col-xs-9">
            <p>%(input)s</p>
            <p>%(clear_template)s</p>
        </div>
    </div></div></div>
    """
    input_template = """
    <a href="#" class="btn btn-default btn-file-input">
        <label for="%(id)s">
            %(input_text)s
            %(input)s
        </label>
    </a>
    """

    def __init__(self, *args, **kwargs):
        self.image_attrs = kwargs.pop('image_attrs', None)
        super().__init__(*args, **kwargs)

    def render(self, name, value, attrs=None):
        substitutions = {
            'initial_text': self.initial_text,
            'input_text': self.input_text,
            'clear_template': '',
            'clear_checkbox_label': self.clear_checkbox_label,
        }
        template = self.template_empty

        input = super(ClearableFileInput, self).render(name, value, attrs)
        substitutions['input'] = self.input_template % {'input': input, 'input_text': self.input_text, 'id': attrs['id']}

        if self.is_initial(value):
            template = self.template_with_initial
            substitutions.update(self.get_template_substitution_values(value))
            substitutions['initial'] = format_html(
                '<img src="{{0}}?{}" {}/>'.format(
                    int(time.time()),
                    " ".join(format_html('{}="{}"', k, v) for k, v in self.image_attrs.items()) if self.image_attrs else ""),
                value.url)
            if not self.is_required:
                checkbox_name = self.clear_checkbox_name(name)
                checkbox_id = self.clear_checkbox_id(checkbox_name)
                substitutions['clear_checkbox_name'] = conditional_escape(checkbox_name)
                substitutions['clear_checkbox_id'] = conditional_escape(checkbox_id)
                substitutions['clear'] = CheckboxInput().render(checkbox_name, False, attrs={'id': checkbox_id})
                substitutions['clear_template'] = self.template_with_clear % substitutions

        return mark_safe(template % substitutions)
