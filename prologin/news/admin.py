# Copyright (C) <2013> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

from django.contrib import admin
from zinnia.models.entry import Entry
from zinnia.admin.entry import EntryAdmin


admin.site.register(Entry, EntryAdmin)
