# Copyright (C) <2016> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

import rules


rules.add_perm('schools.merge', rules.is_staff)
