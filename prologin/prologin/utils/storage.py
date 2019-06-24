# Copyright (C) <2016> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

from django.core.files.storage import get_storage_class


class OverwriteStorage(get_storage_class()):
    """
    Storage that deletes the file before trying to write to it, effectively replacing the file.
    """
    def get_available_name(self, name, max_length=None):
        self.delete(name)
        return name
