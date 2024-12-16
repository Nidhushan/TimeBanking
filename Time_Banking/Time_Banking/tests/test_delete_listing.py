from django.test import TestCase
from django.urls import reverse
from Time_Banking.models import Listing, User
from unittest.mock import patch


class DeleteListingTest(TestCase):
    def setUp(self):
        # Create a user and log them in
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        
        # Create a listing associated with the user
        self.listing = Listing.objects.create(title="Test Listing", creator=self.user)
        
        # Define URL for the delete listing view
        self.url = reverse('delete-listing', args=[self.listing.id])

    def test_delete_listing_success(self):
        # Log in as the user
        self.client.login(username='testuser', password='testpassword')

        # Make POST request to delete the listing
        response = self.client.post(self.url)

        # Check if the listing is deleted (should redirect to 'my_service')
        self.assertRedirects(response, reverse('my_service'))

        # Ensure the listing is actually deleted from the database
        self.assertFalse(Listing.objects.filter(id=self.listing.id).exists())

    def test_delete_listing_invalid_id(self):
        # Log in as the user
        self.client.login(username='testuser', password='testpassword')

        # Try to delete a listing that doesn't exist
        response = self.client.post(reverse('delete-listing', args=[999]))  # Non-existing listing id

        # Check for a 404 error page
        self.assertEqual(response.status_code, 404)

    def test_delete_listing_no_permission(self):
        # Create a second user who is not the owner of the listing
        another_user = User.objects.create_user(username='anotheruser', password='password')
        
        # Log in as the second user
        self.client.login(username='anotheruser', password='password')

        # Attempt to delete the listing owned by the first user
        response = self.client.post(self.url)

        # Check for a permission error or no permission to delete
        self.assertEqual(response.status_code, 403)  # Assuming a 403 is returned for permission denial

    def test_delete_listing_without_login(self):
        # Make a POST request without being logged in
        response = self.client.post(self.url)

        # Check for a redirect to the login page (login_required decorator)
        self.assertRedirects(response, f'/accounts/login/?next={self.url}')

    @patch('your_app.views.Listing.delete')
    def test_delete_listing_exception_handling(self, mock_delete):
        # Simulate an error in the delete operation
        mock_delete.side_effect = Exception('Database error')

        # Log in as the user
        self.client.login(username='testuser', password='testpassword')

        # Make the POST request to delete the listing
        response = self.client.post(self.url)

        # Check that the error response contains the appropriate message
        self.assertEqual(response.status_code, 500)
        self.assertJSONEqual(response.content, {'error': 'Database error'})
