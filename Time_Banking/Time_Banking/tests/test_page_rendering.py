from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from ..models import Listing, Category
from datetime import timedelta
from django.core.files.uploadedfile import SimpleUploadedFile

class RenderPagesTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='password123'
        )
        self.user_settings_url = reverse('user_settings_page')  
        self.create_listing_url = reverse('create_listing_page')
        self.my_service_url = reverse('my_service')

    def test_user_settings_page_redirects_for_unauthenticated_user(self):
        response = self.client.get(self.user_settings_url)
        self.assertEqual(response.status_code, 302)  
        self.assertIn('/login/', response.url)  
    
    def test_user_settings_page_renders_for_authenticated_user(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(self.user_settings_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user_settings.html')
        self.client.logout()
        
    def test_create_listing_page_redirects_for_unauthenticated_user(self):
        response = self.client.get(self.create_listing_url)
        self.assertEqual(response.status_code, 302)  
        self.assertIn('/login/', response.url)  

    def test_create_listing_page_renders_for_authenticated_user(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(self.create_listing_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_listing.html')
        self.client.logout()
        
    def test_get_profile_page_for_authenticated_user(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('profile_info', args=[self.user.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile_info.html')
        self.client.logout()
        
        
    def test_my_service_view(self):
        # Create listings for the user
        self.client.login(username='testuser', password='password123')
        image = SimpleUploadedFile("test_image.jpg", b"file_content", content_type="image/jpeg")  
        listing1 = Listing.objects.create(
            title="Listing 1",
            description="Description 1",
            category=Category.GRAPHICS_DESIGN,
            creator=self.user,
            duration=timedelta(minutes=60),
            listing_type="Offer",
            status="Available",
            image=image,
        )
        listing2 = Listing.objects.create(
            title="Listing 2",
            description="Description 2",
            category=Category.PROGRAMMING_TECH,
            creator=self.user,
            duration=timedelta(minutes=120),
            listing_type="Request",
            status="Pending",
            image=image,
        )

        # Make a GET request to the my_service view
        response = self.client.get(self.my_service_url)

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'myservice.html')
        self.assertIn(listing1, response.context['listings'])
        self.assertIn(listing2, response.context['listings'])
        self.assertEqual(len(response.context['listings']), 2)
        
