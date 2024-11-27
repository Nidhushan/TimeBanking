from django.test import TestCase, Client, override_settings
from ..models import Listing, User, ListingResponse, ListingAvailability, Category, Tag
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import timedelta
import json
from unittest.mock import patch



class UserSettingsTests(TestCase):
    
    Old_password = 'OldPassword123!'
    New_password = 'NewPassword123!'
    
    def setUp(self):
        self.client = Client()
        
        # Create a user for testing
        self.user = User.objects.create_user(username="testuser", password=self.Old_password)
        self.client.login(username="testuser", password=self.Old_password)
        
    def test_change_valid_password(self):
        # Test changing the password with valid data
        response = self.client.post(
            reverse('change_password'), 
            json.dumps({
                "username": "testuser",
                "current_password": self.Old_password,
                "new_password": self.New_password,
                "confirm_password": self.New_password,
            }),
            content_type='application/json' 
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'success'})
        
        self.client.logout()
        login_response = self.client.login(username="testuser", password=self.New_password)
        self.assertTrue(login_response) 

        profile_response = self.client.get(reverse('profile_info'))
        self.assertEqual(profile_response.status_code, 200)
        
    def test_change_invalid_password(self):
        response = self.client.post(
            reverse('change_password'), 
            json.dumps({
                "username": "testuser",
                "current_password": self.Old_password,
                "new_password": "12345678",
                "confirm_password": "12345678",
            }),
            content_type='application/json'  
        )
        
        self.assertEqual(response.status_code, 400)

    
    def test_change_password_with_incorrect_current_password(self):
        response = self.client.post(
            reverse('change_password'), 
            json.dumps({
                "username": "testuser",
                "current_password": "incorrect_password",
                "new_password": self.New_password,
                "confirm_password": self.New_password,
            }),
            content_type='application/json'  
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'error': 'Current password is incorrect'})
        
        
    def test_change_password_not_post(self):
        response = self.client.get(reverse('change_password'))
        self.assertEqual(response.status_code, 405)
    
        
    def test_change_password_with_mismatched_new_passwords(self):
        response = self.client.post(
            reverse('change_password'), 
            json.dumps({
                "username": "testuser",
                "current_password": self.Old_password,
                "new_password": self.New_password,
                "confirm_password": "12345678",
            }),
            content_type='application/json'  
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'error': 'New passwords do not match'})
        
    def test_change_password_not_own(self):
        # Test changing the password of another user
        other_user = User.objects.create_user(username="otheruser", password="password")
        
        response = self.client.post(
            reverse('change_password'), 
            json.dumps({
                "username": "otheruser",
                "current_password": "password",
                "new_password": self.Old_password,
                "confirm_password": self.New_password,
            }),
            content_type='application/json'  
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {'error': 'Not authorized to change password'})
        
        
        
    def test_change_password_missing_fields(self):
        data = {
            'username': 'testuser',
            'new_password': self.New_password,
            'confirm_password': self.New_password
        }  
        response = self.client.post(
            reverse('change_password'), 
            json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)

        self.assertEqual(response.json(), {'error': 'Invalid input, missing fields'})



    def test_change_password_generic_exception(self):
        with patch('Time_Banking.models.User.set_password', side_effect=Exception('Test exception')):
            data = {
                'username': 'testuser',
                'current_password': self.Old_password,
                'new_password': self.New_password,
                'confirm_password': self.New_password
            }
            response = self.client.post(
                reverse('change_password'), 
                json.dumps(data),
                content_type='application/json'
            )

            self.assertEqual(response.status_code, 500)

            self.assertEqual(response.json(), {'error': 'Test exception'})
            
            
        
    # def test_edit_user_settings(self):
    #     image = SimpleUploadedFile("test_image.jpg", b"file_content", content_type="image/jpeg")
    #     response = self.client.post(
    #         reverse('update_user_settings'), 
    #         {
    #             "name": "Test User",
    #             "title": "Test Title",
    #             "location": "New York, NY",
    #             # no change to link and bio
    #             "picture": image
    #         }
    #     )
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.json(), {'status': 'Profile updated successfully'})
    #     user = User.objects.get(username="testuser")
    #     self.assertEqual(user.name, "Test User")
    #     self.assertEqual(user.title, "Test Title")
    #     self.assertEqual(user.location, "New York, NY")
    #     self.assertEqual(user.link, "")
    #     self.assertEqual(user.bio, "")

    def test_get_user_details(self):
        response = self.client.get(
            reverse('user_detail', args=[self.user.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "avg_rating": 0.0,
            "bio": "",
            "email": "",
            "link": "",
            "location": "",
            "multiplier": 1.0,
            "name": "",
            "picture_url": "",
            "title": ""
        })
        
    def test_delete_account(self):
        response = self.client.post(reverse('delete_account'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'Account deleted successfully'})
        
        login_response = self.client.login(username="testuser", password=self.New_password)
        self.assertFalse(login_response)
        
    def test_delete_account_not_post(self):
        response = self.client.get(reverse('delete_account'))
        self.assertEqual(response.status_code, 405)
        
        
    def test_delete_account_exception_handling(self):
        with patch('Time_Banking.models.User.delete', side_effect=Exception('Test exception')):

            self.client.login(username='testuser', password='password123')
            delete_account_url = reverse('delete_account')
            response = self.client.post(delete_account_url)

            self.assertEqual(response.status_code, 500)

            self.assertIn('error', response.json())
            self.assertEqual(response.json()['error'], 'Test exception')
            
            
    def test_user_detail_page_user_found(self):
        response = self.client.get(reverse('user_detail_page', args=[self.user.id]))
        
        self.assertEqual(response.status_code, 200)
        
        self.assertContains(response, self.user.username)

    def test_user_detail_page_user_not_found(self):
        non_existent_user_id = 999  
        response = self.client.get(reverse('user_detail_page', args=[non_existent_user_id]))
        
        self.assertEqual(response.status_code, 200)
        
        self.assertContains(response, 'User not found')
        