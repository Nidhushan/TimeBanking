from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from Time_Banking.forms import ProfileEditForm
from Time_Banking.models import User


class EditProfileViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create a user with initial values
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass",
            name="OldName",
            title="OldTitle",
            location="OldLocation",
            bio="Old bio text",
            link="http://old-link.example.com",
        )
        self.client.login(username="testuser", password="testpass")
        self.edit_profile_url = reverse("edit_profile")
        self.profile_info_url = reverse("profile_info")
        self.delete_profile_picture_url = reverse("delete_profile_picture")

    def test_get_edit_profile_view(self):
        # Test if the edit profile page loads successfully
        response = self.client.get(self.edit_profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "edit_profile.html")
        self.assertIsInstance(response.context["form"], ProfileEditForm)

    def test_post_valid_form_data(self):
        # Test submitting valid data updates the user profile
        # image = SimpleUploadedFile(
        #     "test_image.jpg", b"file_content", content_type="image/jpeg"
        # )
        response = self.client.post(
            self.edit_profile_url,
            {
                "name": "NewName",
                "title": "NewTitle",
                "location": "NewLocation",
                "bio": "New bio text",
                "link": "http://new-link.example.com",
            },
        )
        self.assertRedirects(response, self.profile_info_url)
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, "NewName")
        self.assertEqual(self.user.title, "NewTitle")
        self.assertEqual(self.user.location, "NewLocation")
        self.assertEqual(self.user.bio, "New bio text")
        self.assertEqual(self.user.link, "http://new-link.example.com")

    def test_post_with_invalid_form_data(self):
        # Test submitting invalid data does not update the user profile
        response = self.client.post(
            self.edit_profile_url,
            {
                "name": "",  # Invalid: name cannot be blank
                "title": "NewTitle",
                "location": "NewLocation",
                "bio": "New bio text",
                "link": "invalid-link",  # Invalid: not a proper URL
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "edit_profile.html")
        self.user.refresh_from_db()
        self.assertNotEqual(self.user.name, "")
        self.assertNotEqual(self.user.link, "invalid-link")

    def test_access_without_login(self):
        # Test accessing the page without logging in redirects to login page
        self.client.logout()
        response = self.client.get(self.edit_profile_url)
        self.assertNotEqual(response.status_code, 200)
        self.assertIn("/login/", response.url)

    def test_add_skill_to_user(self):
        # Test adding skills to the user's profile
        skill_name = "Python"
        response = self.client.post(
            self.profile_info_url, {"add_skill": "add_skill", "skills": skill_name}
        )
        self.assertRedirects(response, self.profile_info_url)
        self.user.refresh_from_db()
        self.assertTrue(self.user.skills.filter(name=skill_name).exists())

    def test_delete_profile_picture(self):
        # Test deleting the user's profile picture
        image = SimpleUploadedFile(
            name="test_image.jpg",
            content=b"some_image_content",
            content_type="image/jpeg",
        )
        self.user.picture = image
        self.user.save()

        response = self.client.post(self.delete_profile_picture_url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"success": True})
        self.user.refresh_from_db()
        self.assertEqual(self.user.picture.name, "")

    def test_delete_profile_picture_no_picture(self):
        # Test deleting a profile picture when none exists
        response = self.client.post(self.delete_profile_picture_url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {"success": False, "error": "No profile picture to delete."},
        )

    def test_delete_profile_picture_invalid_method(self):
        # Test sending a GET request to delete_profile_picture
        response = self.client.get(self.delete_profile_picture_url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content, {"success": False, "error": "Invalid request method."}
        )
