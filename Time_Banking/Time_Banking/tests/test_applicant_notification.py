from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from ..models import Notification, ListingResponse, User, Listing, Tag, Category
from datetime import timedelta

class NotificationTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client = Client()
        self.client.login(username='testuser', password='password')

        self.notification = Notification.objects.create(
            user=self.user,
            message="Test Notification",
            is_read=False,
            url="/test-url"
        )

    def test_notification_creation(self):
        self.assertEqual(str(self.notification), f"Notification for {self.user.username} - Test Notification")

    def test_get_notifications(self):
        response = self.client.get(reverse('get_notifications'))
        self.assertEqual(response.status_code, 200)
        self.assertIn("Test Notification", response.json()["notifications"][0]["message"])

    def test_mark_as_read(self):
        response = self.client.post(reverse('mark_as_read', args=[self.notification.id]))
        self.assertEqual(response.status_code, 200)
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)


class ViewApplicantsTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.other_user = User.objects.create_user(username='otheruser', password='password')
        self.client = Client()
        self.client.login(username='testuser', password='password')
        
        self.tag1 = Tag.objects.create(name="Tag1", category=Category.GRAPHICS_DESIGN)
        self.tag2 = Tag.objects.create(name="Tag2", category=Category.GRAPHICS_DESIGN)
        self.listing = Listing.objects.create(
            title="Original Title",
            description="Original Description",
            category=Category.GRAPHICS_DESIGN,
            creator=self.user,
            duration=timedelta(minutes=30),
            listing_type="Offer",
            status="Available",
        )
        self.listing.tags.set([self.tag1, self.tag2])

        self.response1 = ListingResponse.objects.create(
            user=self.user,
            listing_id=1,
            status=0,
            message="Initial"
        )
        self.response2 = ListingResponse.objects.create(
            user=self.other_user,
            listing_id=1,
            status=0,
            message="Initial"
        )

    def test_view_applicants_get(self):
        image = SimpleUploadedFile("test_image.jpg", b"file_content", content_type="image/jpeg")
        response = self.client.get(reverse('view_applicants', args=[1]))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.response1, response.context['responses'])

    def test_view_applicants_post(self):
        post_data = {"response_id": self.response1.id}
        response = self.client.post(reverse('view_applicants', args=[1]), data=post_data)
        self.assertEqual(response.status_code, 302)  # Redirect
        self.response1.refresh_from_db()
        self.assertEqual(self.response1.status, 2)
        self.response2.refresh_from_db()
        self.assertEqual(self.response2.status, 3)

        notification = Notification.objects.filter(user=self.response1.user).first()
        self.assertIsNotNone(notification)
        self.assertEqual(notification.message, "An update on your application.")


class AppliedServicesTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client = Client()
        self.client.login(username='testuser', password='password')

        self.image = SimpleUploadedFile("test_image.jpg", b"file_content", content_type="image/jpeg")
        self.tag1 = Tag.objects.create(name="Tag1", category=Category.GRAPHICS_DESIGN)
        self.tag2 = Tag.objects.create(name="Tag2", category=Category.GRAPHICS_DESIGN)
        self.listing = Listing.objects.create(
            title="Original Title",
            description="Original Description",
            category=Category.GRAPHICS_DESIGN,
            creator=self.user,
            duration=timedelta(minutes=30),
            listing_type="Offer",
            status="Available",
            image=self.image
        )
        self.listing.tags.set([self.tag1, self.tag2])

        self.response = ListingResponse.objects.create(
            user=self.user,
            listing_id=1,
            status=1,
            message="Test response"
        )

    def test_applied_services(self):
        response = self.client.get(reverse('applied_services'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.response, response.context['responses'])
