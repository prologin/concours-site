import django.db.models.signals
from django.contrib.auth import get_user_model
from django.test import TestCase

import forum.models


class ForumSetupMixin:
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        django.db.models.signals.post_save.receivers = []

    def setUp(self):
        self.u1 = get_user_model().objects.create(username="joseph", email="joseph@example.org")
        self.u2 = get_user_model().objects.create(username="marchand", email="marchand@example.org")
        self.u3 = get_user_model().objects.create(username="dieu", email="dieu@example.org", is_staff=True)

        self.f1 = forum.models.Forum.objects.create(
            id=1, name="Test forum", description="Un super forum")
        self.t11 = forum.models.Thread.objects.create(
            forum=self.f1, title="Tout est cassé")
        self.p111 = forum.models.Post.objects.create(
            thread=self.t11, author=self.u1, content="Rien ne marche !")
        self.p112 = forum.models.Post.objects.create(
            thread=self.t11, author=self.u2, content="C'est horrible !")

        self.f2 = forum.models.Forum.objects.create(
            id=2, name="[STAFF] Privé", description="Très secret")
        self.t21 = forum.models.Thread.objects.create(
            forum=self.f2, title="Prologin est génial")
        self.p211 = forum.models.Post.objects.create(
            thread=self.t21, author=self.u3, content="Tout est parfait !")


class ForumAnonymousTestCase(ForumSetupMixin, TestCase):
    def testListForum(self):
        page = self.client.get("/forum/")
        self.assertContains(page, "Test forum")
        self.assertNotContains(page, "[STAFF] Privé")

    def testWrongSlugRedirect(self):
        page = self.client.get(f"/forum/forum-wrong-slug-1/thread-wrong-slug-{self.t11.pk}/")
        self.assertRedirects(page, f"/forum/test-forum-1/tout-est-casse-{self.t11.pk}/")

    def testListThreads(self):
        page = self.client.get("/forum/test-forum-1")
        self.assertContains(page, "Tout est cassé")
        self.assertContains(page, "joseph")

    def testStaffForumInaccessible(self):
        page = self.client.get("/forum/staff-forum-2")
        self.assertEqual(page.status_code, 302)
        self.assertIn("login", page.get("Location"))

    def testListThreadPosts(self):
        page = self.client.get(f"/forum/test-forum-1/tout-est-casse-{self.t11.pk}/")
        self.assertContains(page, "Tout est cassé")
        self.assertContains(page, "Rien ne marche")
        self.assertContains(page, "C'est horrible")
        # You have to login…
        self.assertContains(page, "to post messages")


class ForumUserTestCase(ForumSetupMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.u1)

    def testThreadViewHasEditAndCiteLinks(self):
        page = self.client.get(f"/forum/test-forum-1/tout-est-casse-{self.t11.pk}/")
        self.assertContains(page, "Compose your message here")
        self.assertContains(page, f"/forum/post/tout-est-casse/{self.p111.pk}/edit")
        self.assertContains(page, f"/forum/post/tout-est-casse/{self.p111.pk}/cite")


class ForumStaffTestCase(ForumSetupMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.u3)

    def testCanSeeStaffForum(self):
        page = self.client.get("/forum/")
        self.assertContains(page, "[STAFF] Privé")
        self.assertContains(page, "Très secret")
        self.assertContains(page, "dieu")

    def testCanSeeStaffForumThreads(self):
        page = self.client.get("/forum/staff-prive-2")
        self.assertContains(page, "Prologin est génial")
        self.assertContains(page, "dieu")

    def testHasModerationActions(self):
        page = self.client.get(f"/forum/test-forum-1/tout-est-casse-{self.t11.pk}/")
        self.assertContains(page, f"/forum/post/tout-est-casse/{self.p111.pk}/edit")
        self.assertContains(page, f"/forum/post/tout-est-casse/{self.p111.pk}/edit/visibility")
        self.assertContains(page, f"/forum/post/tout-est-casse/{self.p111.pk}/delete")
        self.assertContains(page, f"/forum/post/tout-est-casse/{self.p112.pk}/edit")
        self.assertContains(page, f"/forum/post/tout-est-casse/{self.p112.pk}/edit/visibility")
        self.assertContains(page, f"/forum/post/tout-est-casse/{self.p112.pk}/delete")

    def testDeleteNonHeadPost(self):
        page = self.client.get(f"/forum/post/tout-est-casse/{self.p112.pk}/delete")
        self.assertContains(page, "Are you sure you want to delete")
        self.assertContains(page, "Tout est cassé")
        self.assertContains(page, "marchand")
        page = self.client.post(f"/forum/post/tout-est-casse/{self.p112.pk}/delete")
        self.assertRedirects(page, f"/forum/test-forum-1/tout-est-casse-{self.t11.pk}/")

    def testDeleteHeadPost(self):
        page = self.client.get(f"/forum/post/tout-est-casse/{self.p111.pk}/delete")
        self.assertContains(page, "Are you sure you want to delete")
        self.assertContains(page, "Tout est cassé")
        self.assertContains(page, "joseph")
        page = self.client.post(f"/forum/post/tout-est-casse/{self.p111.pk}/delete")
        self.assertEqual(page.status_code, 302)
        url = f"/forum/test-forum-1/tout-est-casse-{self.t11.pk}/"
        self.assertRedirects(page, "/forum/test-forum-1")
        page = self.client.get(url)
        self.assertEqual(page.status_code, 404)
