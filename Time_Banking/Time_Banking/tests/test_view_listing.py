import json
from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.formats import date_format

from ..models import Category, Listing, Tag, User


class ViewListingTests(TestCase):

    def setUp(self):
        self.client = Client()

        # Create the listing creator
        self.creator_user = User.objects.create_user(
            username="creatoruser", password="password"
        )

        # Log in as a different user for testing
        self.user = User.objects.create_user(username="testuser", password="password")
        self.client.login(username="testuser", password="password")

        # Create tags
        self.tag1 = Tag.objects.create(name="Django")
        self.tag2 = Tag.objects.create(name="Web Development")

        # Create a listing with the creator user
        self.listing = Listing.objects.create(
            creator=self.creator_user,
            title="Test Listing",
            category=Category.WRITING_TRANSLATION,
            description="This is a test description for the listing.",
            image=SimpleUploadedFile(
                "test_image.jpg", b"file_content", content_type="image/jpeg"
            ),
            listing_type=True,
            duration=timedelta(hours=2),
        )
        self.listing.tags.set([self.tag1, self.tag2])  # Add tags to the listing

    def test_view_listing_page_loads_correctly(self):
        # Test if the listing page loads correctly with valid data
        response = self.client.get(reverse("view_listing", args=[self.listing.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "view_listing.html")
        self.assertContains(response, self.listing.title)
        self.assertContains(response, self.listing.description)
        self.assertContains(response, self.listing.get_category_display())
        self.assertContains(response, self.tag1.name)
        self.assertContains(response, self.tag2.name)

    def test_view_listing_with_non_existent_listing(self):
        # Test loading a non-existent listing
        response = self.client.get(reverse("view_listing", args=[9999]))
        self.assertEqual(response.status_code, 404)  # Should return a 404 error

    def test_view_listing_without_authentication(self):
        # Test accessing the listing page without authentication
        self.client.logout()  # Ensure the user is logged ou
        response = self.client.get(reverse("view_listing", args=[self.listing.id]))
        self.assertEqual(
            response.status_code, 200
        )  # Should allow public access if that’s the requiremen

    def test_view_listing_with_invalid_listing_id(self):
        # Pass a non-existent numeric ID
        response = self.client.get(reverse("view_listing", args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_view_listing_displays_all_fields_correctly(self):
        response = self.client.get(reverse("view_listing", args=[self.listing.id]))

        # Generate expected date using date_format for consistency
        expected_date = date_format(self.listing.posted_at, format="N j, Y, P")
        # print("Expected Date:", expected_date)
        # print("Response Content:", response.content.decode())

        # Assertions to check details
        self.assertContains(response, "Test Listing")  # Check title
        self.assertContains(
            response, "This is a test description for the listing."
        )  # Check description
        self.assertContains(
            response, self.listing.get_category_display()
        )  # Check category display
        self.assertContains(response, "2:00:00")  # Check duration
        self.assertContains(response, expected_date)  # Check formatted date

    def test_view_listing_contains_accept_button(self):
        # Test that the "Accept Service/Request" button is presen
        response = self.client.get(reverse("view_listing", args=[self.listing.id]))
        self.assertContains(response, "Apply Service/Request")
        self.assertContains(response, 'type="submit"')  # Check if submit button exists

    def test_view_listing_image_display(self):
        # Test that the listing image is displayed correctly
        response = self.client.get(reverse("view_listing", args=[self.listing.id]))
        self.assertContains(
            response, self.listing.image.url
        )  # Check if image URL is in the response

    def test_view_listing_displays_multiple_tags(self):
        # Verify that multiple tags are displayed correctly on the page
        response = self.client.get(reverse("view_listing", args=[self.listing.id]))
        self.assertContains(response, self.tag1.name)
        self.assertContains(response, self.tag2.name)

    def test_view_listing_redirects_on_post_request(self):
        response = self.client.post(reverse("view_listing", args=[self.listing.id]))
        self.assertEqual(
            response.status_code, 405
        )  # Expecting 405 (Method Not Allowed) for POST requests

    # def test_view_listing_accept_service_redirects_properly(self):
    #     response = self.client.post(reverse('accept_service', args=[self.listing.id]))
    #     self.assertEqual(response.status_code, 200)
    #     self.assertJSONEqual(response.content, {'message': 'Service/Request accepted successfully!'})

    def test_view_all_listings_api(self):
        response = self.client.get(reverse("get_all_listings"))
        r = json.loads(response.content)
        self.assertEqual(r[0]["category"], self.listing.category.label)
        self.assertEqual(r[0]["creator"], self.listing.creator.username)
        self.assertEqual(r[0]["description"], self.listing.description)
        self.assertEqual(r[0]["duration"], "2:00:00")
        self.assertEqual(r[0]["image"], self.listing.image.url)
        self.assertEqual(r[0]["listing_type"], "True")
        self.assertEqual(r[0]["tags"], [self.tag1.name, self.tag2.name])
        self.assertEqual(r[0]["title"], self.listing.title)

    # def test_view_listing_api(self):
    #     response = self.client.get(reverse("get_listing_by_id"))
    #     r = json.loads(response.content)
    #     self.assertEqual(r["category"], self.listing.category.label)
    #     self.assertEqual(r["creator"], self.listing.creator.username)
    #     self.assertEqual(r["description"], self.listing.description)
    #     self.assertEqual(r["duration"], "2:00:00")
    #     self.assertEqual(r["image"], self.listing.image.url)
    #     self.assertEqual(r["listing_type"], "True")
    #     self.assertEqual(r["tags"], [self.tag1.name, self.tag2.name])
    #     self.assertEqual(r["title"], self.listing.title)
