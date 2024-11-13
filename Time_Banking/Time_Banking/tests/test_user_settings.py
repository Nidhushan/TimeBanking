from django.test import TestCase, Client, override_settings
from ..models import Listing, User, ListingResponse, ListingAvailability, Category, Tag
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import timedelta
import tempfile
import shutil
import random
import json


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
                "current_password": self.New_password,
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
                "current_password": self.New_password,
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
                "new_password": self.New_password,
                "confirm_password": self.New_password,
            }),
            content_type='application/json'  
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {'error': 'Not authorized to change password'})
        
        
    def test_delete_account(self):
        response = self.client.post(reverse('delete_account'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'Account deleted successfully'})
        
        login_response = self.client.login(username="testuser", password=self.New_password)
        self.assertFalse(login_response)
        
    def test_delete_account_not_post(self):
        response = self.client.get(reverse('delete_account'))
        self.assertEqual(response.status_code, 405)
        
        