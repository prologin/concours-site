from django import forms


class NewableModelChoiceField(forms.ModelChoiceField):
    def to_python(self, value):
        try:
            return super().to_python(value)
        except forms.ValidationError as exc:
            return self.create_new(self.queryset.model, value, exc)

    def create_new(self, model, value, exc):
        raise NotImplementedError()
