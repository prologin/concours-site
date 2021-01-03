from django.urls import reverse
from django.test import TestCase

from .models import OpenIDClientPolicy
from oidc_provider.models import Client as OIDCClient
from . import oidc_authz
from django.contrib.auth import get_user_model
from django.conf import settings

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

class OIDCAuthorizationTest(TestCase):

    def setUp(self):
        from contest.models import Edition
        from datetime import datetime, timedelta
        self.oidc_client = OIDCClient(name="test_client")
        self.oidc_client.save()
        self.user = get_user_model()(username="test")
        self.user.save()
        self.edition = Edition(year=settings.PROLOGIN_EDITION, date_begin=datetime.now(), date_end=datetime.now() + timedelta(days=365))
        self.edition.save()
    
    def test_allowed_in_client_without_policy(self):
        self.assertEqual(oidc_authz.authorize(None, self.user, self.oidc_client), None)
    
    def test_not_allowed_in_client_with_empty_policy(self):
        from django.core.exceptions import PermissionDenied
        policy = OpenIDClientPolicy(openid_client=self.oidc_client)
        policy.save()

        with self.assertRaises(PermissionDenied):
            oidc_authz.authorize(None, self.user, self.oidc_client)
        
        policy.delete()
    
    def test_staff_allowed_in_staff_only_policy(self):
        policy = OpenIDClientPolicy(openid_client=self.oidc_client, allow_staff=True)
        user = get_user_model()(username="staff_test", email="test@staff.net", is_staff=True)
        user.save()

        self.assertTrue(policy.is_user_allowed(user))

        user.delete()
    
    def test_non_staff_not_allowed_in_staff_only_policy(self):
        policy = OpenIDClientPolicy(openid_client=self.oidc_client, allow_staff=True)
        user = get_user_model()(username="not_staff", email="not@staff.net")
        user.save()
        
        self.assertTrue(not policy.is_user_allowed(user))

        user.delete()
    
    def test_group_member_in_group_allowed(self):
        from django.contrib.auth.models import Group
        group = Group(name="allowed_group")
        other_group = Group(name="other_group")
        group.save()
        other_group.save()

        policy = OpenIDClientPolicy(openid_client=self.oidc_client)
        policy.allow_groups.set([group, other_group])
        policy.save()
        
        user = get_user_model()(username="group_member", email="member@group.net")
        user.save()
        user.groups.set([group])
        user.save()

        self.assertTrue(policy.is_user_allowed(user))

        other_group.delete()
        group.delete()
        user.delete()
        policy.delete()
    
    def test_not_group_member_in_group_allowed(self):
        from django.contrib.auth.models import Group
        group = Group(name="allowed_group2")
        group.save()
        policy = OpenIDClientPolicy(openid_client=self.oidc_client)
        policy.save()
        policy.allow_groups.set([group])
        
        user = get_user_model()(username="not_group_member", email="not_member@group.net")
        user.save()
        self.assertTrue(not policy.is_user_allowed(user))

        group.delete()
        user.delete()
        policy.delete()
    
    def test_assigned_semifinal_in_assigned_semifinal(self):
        from contest.models import Contestant
        user = get_user_model()(username="oo", email="semifinalist@contestants.net")
        user.save()
        contestant = Contestant(edition=self.edition, user=user, assignation_semifinal=2)
        contestant.save()
        policy = OpenIDClientPolicy(openid_client=self.oidc_client, allow_assigned_semifinal=True)
        policy.save()
        
        self.assertTrue(policy.is_user_allowed(user))

        user.delete()
        policy.delete()
    
    def test_not_assigned_semifinal_in_assigned_semifinal(self):
        from contest.models import Contestant
        user = get_user_model()(username="oo", email="semifinalist@contestants.net")
        user.save()
        contestant = Contestant(edition=self.edition, user=user)
        contestant.save()
        policy = OpenIDClientPolicy(openid_client=self.oidc_client, allow_assigned_semifinal=True)
        policy.save()
        
        self.assertFalse(policy.is_user_allowed(user))

        user.delete()
        policy.delete()
    
    def test_assigned_final_in_assigned_final(self):
        from contest.models import Contestant
        user = get_user_model()(username="oo", email="semifinalist@contestants.net")
        user.save()
        contestant = Contestant(edition=self.edition, user=user, assignation_final=2)
        contestant.save()
        policy = OpenIDClientPolicy(openid_client=self.oidc_client, allow_assigned_final=True)
        
        self.assertTrue(policy.is_user_allowed(user))

        user.delete()
        policy.delete()
    
    def test_not_assigned_final_in_assigned_final(self):
        from contest.models import Contestant
        user = get_user_model()(username="oo", email="semifinalist@contestants.net")
        user.save()
        contestant = Contestant(edition=self.edition, user=user, assignation_final=0)
        contestant.save()
        policy = OpenIDClientPolicy(openid_client=self.oidc_client, allow_assigned_final=True)
        policy.save()
        
        self.assertFalse(policy.is_user_allowed(user))

        user.delete()
        policy.delete()
