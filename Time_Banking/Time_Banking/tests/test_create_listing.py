from django.test import TestCase, Client, override_settings
from ..models import Listing, User, ListingResponse, ListingAvailability, Category, Tag
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import timedelta
import tempfile
import shutil

TEMP_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT) # make sure the image is saved in the temp directory
class CreateListingViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="password")
        self.client.login(username="testuser", password="password")
        
        self.tag1 = Tag.objects.create(name="Tag1")
        self.tag2 = Tag.objects.create(name="Tag2")
        
        
    def test_create_listing_with_valid_data(self):
        # Prepare a valid request payload
        image = SimpleUploadedFile("test_image.jpg", b"file_content", content_type="image/jpeg")
        data = {
            'title': 'Test Listing',
            'category': Category.GRAPHICS_DESIGN,  # Use TextChoices
            'description': 'This is a test description',
            'image': image,
            'listing_type': 'True',
            'duration': '2',
            'tags': [self.tag1.id, self.tag2.id],
        }

        response = self.client.post(reverse('create_listing'), data)
        
        # print(response.json())  # print response for debugging

        # Verify that listing was created successfully
        self.assertEqual(response.status_code, 201)
        self.assertIn('id', response.json())
        self.assertEqual(response.json()['title'], 'Test Listing')

        
        self.assertQuerySetEqual(response.json()['tags'], [str(self.tag1), str(self.tag2)], ordered=False)
        
        
    def test_create_listing_with_missing_required_fields(self):
        title = 'Test Listing'
        category = Category.GRAPHICS_DESIGN
        description = 'This is a test description'
        listing_type = 'True'
        duration = '2'
        image = SimpleUploadedFile("test_image.jpg", b"file_content", content_type="image/jpeg")

        for i in range(6):
            data = {
                'title': title,
                'category': category,
                'description': description,
                'listing_type': listing_type,
                'duration': duration,
                'image': image,
            }

            # Remove a required field from the data
            del data[list(data.keys())[i]]

            response = self.client.post(reverse('create_listing'), data)

            # Verify response status and error message
            self.assertNotEqual(response.status_code, 201)
            self.assertIn('error', response.json())
            self.assertTrue('Missing required fields' in response.json()['error'])
        
        
    def test_create_listing_with_duration(self):
        # Invalid duration format (non-integer)
        image = SimpleUploadedFile("test_image.jpg", b"file_content", content_type="image/jpeg")

        invalid_duration_field = ['two', '2.5', '2.0', '2.5h', '2h30m', '2h 30m', '2 hours', '2 hours 30 minutes']
        for duration in invalid_duration_field:
            data = {
                'title': 'Test Listing',
                'category': Category.PROGRAMMING_TECH,
                'description': 'This is a test description',
                'listing_type': 'True',
                'duration': duration,
                'image': image,
            }
            
            response = self.client.post(reverse('create_listing'), data)

            # Verify response status and error message
            self.assertNotEqual(response.status_code, 201)
            self.assertIn('error', response.json())

        right_duration = ['2', '30', '60', '120']
        for duration in right_duration:
            data = {
                'title': 'Test Listing',
                'category': Category.PROGRAMMING_TECH,
                'description': 'This is a test description',
                'listing_type': 'True',
                'duration': duration,
                'image': image,
            }
            
            response = self.client.post(reverse('create_listing'), data)

            # Verify response status and error message
            self.assertEqual(response.status_code, 201)
            self.assertIn('id', response.json())
            self.assertEqual(response.json()['title'], 'Test Listing')
            
            
    def test_create_listing_with_exceeding_description_length(self):
        # Description exceeding 5000 characters
        image = SimpleUploadedFile("test_image.jpg", b"file_content", content_type="image/jpeg")
        data = {
            'title': 'Test Listing',
            'category': Category.DIGITAL_MARKETING,
            'description': 'a' * 5001,  # Too long
            'listing_type': 'True',
            'duration': '2',
            'image': image,
        }

        response = self.client.post(reverse('create_listing'), data)

        # Verify response status and error message
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
        self.assertEqual(response.json()['error'], 'Description is too long')


    def test_create_listing_with_non_post_request(self):
        # Simulate a GET request
        response = self.client.get(reverse('create_listing'))
        
        # Verify that only POST is allowed
        self.assertEqual(response.status_code, 405)
        self.assertIn('error', response.json())
        self.assertEqual(response.json()['error'], 'POST request required')
        