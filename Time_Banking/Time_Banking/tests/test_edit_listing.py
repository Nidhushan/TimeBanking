from datetime import timedelta
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Category, Listing, Tag, User


class EditListingViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="password")
        self.other_user = User.objects.create_user(
            username="otheruser", password="password"
        )
        self.client.login(username="testuser", password="password")

        # Create tags associated with categories
        self.tag1 = Tag.objects.create(name="Tag1", category=Category.GRAPHICS_DESIGN)
        self.tag2 = Tag.objects.create(name="Tag2", category=Category.GRAPHICS_DESIGN)

        # Create a listing
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

    def test_edit_listing_with_valid_data(self):
        image = SimpleUploadedFile(
            "test_image.jpg", b"file_content", content_type="image/jpeg"
        )
        data = {
            "title": "Updated Title",
            "description": "Updated Description",
            "category": Category.PROGRAMMING_TECH,
            "duration": "45",
            "listing_type": "Request",
            "status": "Fulfilled",
            "tags": [self.tag1.id],
            "image": image,
        }

        response = self.client.post(
            reverse("edit_listing", args=[self.listing.id]), data
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], "Updated Title")

    def test_edit_listing_page_renders(self):
        self.client.login(username="testuser", password="password")
        response = self.client.get(reverse("edit_listing_page", args=[self.listing.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "edit_listing.html")

    def test_edit_listing_as_non_creator(self):
        self.client.login(username="otheruser", password="password")
        response = self.client.get(reverse("edit_listing_page", args=[self.listing.id]))

        self.assertEqual(response.status_code, 403)
        self.assertIn("error", response.json())
        self.assertEqual(
            response.json()["error"], "You can only edit your own service/request."
        )

    def test_edit_listing_with_missing_fields(self):
        image = SimpleUploadedFile(
            "test_image.jpg", b"file_content", content_type="image/jpeg"
        )
        data = {
            "description": "Updated Description",
            "category": Category.GRAPHICS_DESIGN,
            "duration": "45",
            "listing_type": "Request",
            "status": "Fulfilled",
            "image": image,
        }

        response = self.client.post(
            reverse("edit_listing", args=[self.listing.id]), data
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())
        self.assertTrue("Missing required fields" in response.json()["error"])

    def test_edit_listing_with_invalid_duration(self):
        image = SimpleUploadedFile(
            "test_image.jpg", b"file_content", content_type="image/jpeg"
        )
        data = {
            "title": "Updated Title",
            "description": "Updated Description",
            "category": Category.PROGRAMMING_TECH,
            "duration": "invalid",
            "listing_type": "Request",
            "status": "Fulfilled",
            "tags": [self.tag1.id],
            "image": image,
        }

        response = self.client.post(
            reverse("edit_listing", args=[self.listing.id]), data
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())
        self.assertEqual(response.json()["error"], "Duration must be a valid integer")

    def test_edit_listing_with_invalid_listing_type(self):
        image = SimpleUploadedFile(
            "test_image.jpg", b"file_content", content_type="image/jpeg"
        )
        data = {
            "title": "Updated Title",
            "description": "Updated Description",
            "category": Category.GRAPHICS_DESIGN,
            "duration": "45",
            "listing_type": "InvalidType",
            "status": "Fulfilled",
            "tags": [self.tag1.id],
            "image": image,
        }

        response = self.client.post(
            reverse("edit_listing", args=[self.listing.id]), data
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())
        self.assertEqual(response.json()["error"], "Invalid listing type.")

    def test_edit_listing_with_exceeding_description_length(self):
        image = SimpleUploadedFile(
            "test_image.jpg", b"file_content", content_type="image/jpeg"
        )
        data = {
            "title": "Updated Title",
            "description": "a" * 1001,
            "category": Category.GRAPHICS_DESIGN,
            "duration": "45",
            "listing_type": "Request",
            "status": "Fulfilled",
            "tags": [self.tag1.id],
            "image": image,
        }

        response = self.client.post(
            reverse("edit_listing", args=[self.listing.id]), data
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())
        self.assertEqual(response.json()["error"], "Description is too long")

    def test_edit_listing_post_request_required(self):
        # Test that a POST request is required
        response = self.client.get(
            reverse("edit_listing", kwargs={"listing_id": self.listing.id})
        )
        self.assertEqual(response.status_code, 405)
        self.assertJSONEqual(response.content, {"error": "POST request required"})

    def test_edit_listing_internal_server_error(self):
        # Simulate an internal server error
        image = SimpleUploadedFile(
            "test_image.jpg", b"file_content", content_type="image/jpeg"
        )
        with patch(
            "Time_Banking.models.Listing.save", side_effect=Exception("Test exception")
        ):
            response = self.client.post(
                reverse("edit_listing", args=[self.listing.id]),
                {
                    "title": "Updated Title",
                    "description": "Updated Description",
                    "category": Category.PROGRAMMING_TECH,
                    "duration": "45",
                    "listing_type": "Request",
                    "status": "Fulfilled",
                    "tags": [self.tag1.id],
                    "image": image,
                },
            )

            self.assertEqual(response.status_code, 500)
            self.assertIn("error", response.json())
            self.assertEqual(response.json()["error"], "Test exception")
