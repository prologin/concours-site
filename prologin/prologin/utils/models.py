import io
import os
import warnings
from PIL.Image import DecompressionBombWarning
from django.core.files import File
from django.db import models
from wand.exceptions import MissingDelegateError
from wand.image import Image


class ResizeOnSaveImageField(models.ImageField):
    def __init__(self, fit_into=None, *args, **kwargs):
        if isinstance(fit_into, int):
            fit_into = (fit_into, fit_into)
        elif len(fit_into) != 2:
            raise ValueError("fit_into must be an dimension or a pair of dimensions")
        assert fit_into[0] > 0 and fit_into[1] > 0
        self.fit_into = fit_into
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs['fit_into'] = self.fit_into
        return name, path, args, kwargs

    def pre_save(self, model_instance, add):
        file = super().pre_save(model_instance, add)
        if file:
            file.open()
            with warnings.catch_warnings():
                warnings.simplefilter("error", DecompressionBombWarning)
                try:
                    im = Image(file=file)
                except MissingDelegateError:
                    file.seek(0)
                    im = Image(file=file, format=os.path.splitext(file.name)[1].strip(os.path.extsep))
            file.close()
            im.transform(resize='{}x{}>'.format(*self.fit_into))
            buf = io.BytesIO()
            im.save(file=buf)
            file.save(file.name, File(buf, name=file.name), save=False)
        return file
