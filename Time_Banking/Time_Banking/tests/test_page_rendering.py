from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

class UserPagesTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='password123'
        )
        self.user_settings_url = reverse('user_settings_page')  
        self.create_listing_url = reverse('create_listing_page')

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

