# Copyright (C) <2012> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

from django.urls import reverse

from prologin import tests


class TeamTest(tests.WithOrgaUserMixin, tests.ProloginTestCase):
    def test_404(self):
        self.assertInvalidResponse(self.client.get(reverse('team:year', args=(1999,))))

    def test_content(self):
        response = self.client.get(reverse('team:year', args=(self.edition_year,)))
        self.assertIn(self.orga_user.username, response.content.decode())
        self.assertIn(self.orga_user.get_full_name(), response.content.decode())
        self.assertValidResponse(response)
