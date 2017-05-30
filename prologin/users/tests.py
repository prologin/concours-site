from django.core.urlresolvers import reverse

from prologin import tests


class UsersTest(tests.WithContestantMixin, tests.WithOrgaUserMixin, tests.ProloginTestCase):
    def test_profile_visibility(self):
        response = self.client.get(reverse('users:profile', args=[self.contestant.id]))
        self.assertValidResponse(response)
        content = response.content.decode()
        self.assertNotIn(self.contestant.last_name, content)
        self.assertNotIn(self.contestant.phone, content)

        with self.user_login(self.contestant):
            response = self.client.get(reverse('users:profile', args=[self.contestant.id]))
            self.assertValidResponse(response)
            content = response.content.decode()
            self.assertIn(self.contestant.last_name, content)
            self.assertIn(self.contestant.phone, content)

    def test_404(self):
        self.assertInvalidResponse(
            self.client.get(reverse('users:profile', args=(4242,))))

    def test_edit_profile_permission(self):
        self.assertInvalidResponse(self.client.get(
            reverse('users:edit', args=[self.contestant.id])))

        with self.user_login(self.contestant):
            self.assertValidResponse(self.client.get(
                reverse('users:edit', args=[self.contestant.id])))

        with self.user_login(self.orga_user):
            self.assertInvalidResponse(self.client.get(
                reverse('users:edit', args=[self.contestant.id])))
