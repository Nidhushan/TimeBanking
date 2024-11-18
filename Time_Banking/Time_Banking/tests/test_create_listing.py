from django.test import TestCase, Client, override_settings
from ..models import Listing, User, ListingResponse, ListingAvailability, Category, Tag
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import timedelta
import tempfile
import shutil
import random

TEMP_MEDIA_ROOT = tempfile.mkdtemp()


class CreateListingViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="password")
        self.client.login(username="testuser", password="password")
        
        self.tag1 = Tag.objects.create(name="Tag1")
        self.tag2 = Tag.objects.create(name="Tag2")
        
        
    @override_settings(DISABLE_RATE_LIMIT_CHECK=True)
    def test_create_listing_with_valid_data(self):
        # Prepare a valid request payload
        image = SimpleUploadedFile("test_image.jpg", b"file_content", content_type="image/jpeg")
        data = {
            'title': 'Test Listing with valid data',
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
        self.assertEqual(response.json()['title'], 'Test Listing with valid data')
        self.assertEqual(response.json()['description'], 'This is a test description')
    
        self.assertEqual(response.json()['listing_type'], 'Offer')
        self.assertEqual(response.json()['duration'], '2:00:00')

        self.assertQuerySetEqual(response.json()['tags'], [str(self.tag1), str(self.tag2)], ordered=False)
        Listing.objects.all().delete()
        
        
    @override_settings(DISABLE_RATE_LIMIT_CHECK=True)
    def test_create_listing_with_random_data(self):
        # Prepare a valid request payload
        image = SimpleUploadedFile("test_image.jpg", b"file_content", content_type="image/jpeg")
        used_titles = []
        # Randomize the data
        for _ in range(10):
            title = 'Test Listing with random data' + str(random.randint(1, 1000))
            if title in used_titles:
                continue
            used_titles.append(title)
            category = random.choice(Category.choices)[0]
            description = 'This is a test description ' + str(random.randint(1, 10000000000))
            listing_type = random.choice(['True', 'False'])
            duration = str(random.randint(1, 10))
            tags = [self.tag1.id, self.tag2.id]
            
            data = {
                'title': title,
                'category': category,
                'description': description,
                'image': image,
                'listing_type': listing_type,
                'duration': duration,
                'tags': tags,
            }
            
            response = self.client.post(reverse('create_listing'), data)
            
            # print(response.json())  # print response for debugging

            # Verify that listing was created successfully
            self.assertEqual(response.status_code, 201)
            self.assertIn('id', response.json())
            self.assertEqual(response.json()['title'], title)
            self.assertEqual(response.json()['description'], description)
            listing_type = "Offer" if listing_type == 'True' else "Request"
            self.assertEqual(response.json()['listing_type'], listing_type)
            self.assertEqual(response.json()['duration'], str(timedelta(hours=int(duration))))
            self.assertQuerySetEqual(response.json()['tags'], [str(self.tag1), str(self.tag2)], ordered=False)
            
        Listing.objects.all().delete()
        
        
    @override_settings(DISABLE_RATE_LIMIT_CHECK=True)
    def test_create_listing_with_missing_required_fields(self):
        
        category = Category.GRAPHICS_DESIGN
        description = 'This is a test description'
        listing_type = 'Offer'
        duration = '2'
        image = SimpleUploadedFile("test_image.jpg", b"file_content", content_type="image/jpeg")
        used_titles = []
        for i in range(6):
            titles = 'Test Listing with missing field' + str(random.randint(1, 1000))
            while titles in used_titles:
                titles = 'Test Listing with missing field' + str(random.randint(1, 1000))
            used_titles.append(titles)
            data = {
                'title': titles,
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
        Listing.objects.all().delete()
        
        
    @override_settings(DISABLE_RATE_LIMIT_CHECK=True)
    def test_create_listing_with_duration(self):
        # Invalid duration format (non-integer)
        image = SimpleUploadedFile("test_image.jpg", b"file_content", content_type="image/jpeg")

        invalid_duration_field = ['two', '2.5', '2.0', '2.5h', '2h30m', '2h 30m', '2 hours', '2 hours 30 minutes']
        used_titles = []
        for duration in invalid_duration_field:
            titles = 'Test Listing with invalid duration' + str(random.randint(1, 1000))
            while titles in used_titles:
                titles = 'Test Listing with invalid duration' + str(random.randint(1, 1000))
            used_titles.append(titles)
            data = {
                'title': titles,
                'category': Category.PROGRAMMING_TECH,
                'description': 'This is a test description',
                'listing_type': 'Offer',
                'duration': duration,
                'image': image,
            }
            
            response = self.client.post(reverse('create_listing'), data)

            # Verify response status and error message
            self.assertNotEqual(response.status_code, 201)
            self.assertIn('error', response.json())

        right_duration = ['2', '30', '60', '120']
        used_titles = []
        for duration in right_duration:
            titles = 'Test Listing  with different duration ' + str(random.randint(1, 1000))
            while titles in used_titles:
                titles = 'Test Listing with different duration ' + str(random.randint(1, 1000))
            used_titles.append(titles)
            data = {
                'title': titles,
                'category': Category.PROGRAMMING_TECH,
                'description': 'This is a test description',
                'listing_type': 'Offer',
                'duration': duration,
                'image': image,
            }
            
            response = self.client.post(reverse('create_listing'), data)

            # Verify response status and error message
            self.assertEqual(response.status_code, 201)
            self.assertIn('id', response.json())
            self.assertEqual(response.json()['duration'], str(timedelta(hours=int(duration))))
        Listing.objects.all().delete()
            
            
    @override_settings(DISABLE_RATE_LIMIT_CHECK=True)
    def test_create_listing_with_exceeding_description_length(self):
        # Description exceeding 5000 characters
        image = SimpleUploadedFile("test_image.jpg", b"file_content", content_type="image/jpeg")
        data = {
            'title': 'Test Listing',
            'category': Category.DIGITAL_MARKETING,
            'description': 'a' * 5001,  # Too long
            'listing_type': 'Offer',
            'duration': '2',
            'image': image,
        }

        response = self.client.post(reverse('create_listing'), data)

        # Verify response status and error message
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
        self.assertEqual(response.json()['error'], 'Description is too long')
        Listing.objects.all().delete()


    def test_create_listing_with_non_post_request(self):
        # Simulate a GET request
        response = self.client.get(reverse('create_listing'))
        
        # Verify that only POST is allowed
        self.assertEqual(response.status_code, 405)
        self.assertIn('error', response.json())
        self.assertEqual(response.json()['error'], 'POST request required')
        Listing.objects.all().delete()
        
    
    def test_create_listing_with_too_frequent_requests(self):
        # Prepare a valid request payload
        image = SimpleUploadedFile("test_image.jpg", b"file_content", content_type="image/jpeg")
        datas = []
        used_titles = []
        
        for i in range(10):
            titles = 'Test Listing with too frequent test' + str(random.randint(1, 1000000))
            while titles in used_titles:
                titles = 'Test Listing with too frequent test' + str(random.randint(1, 1000000))
            used_titles.append(titles)
            datas.append({
                'title': titles,
                'category': Category.GRAPHICS_DESIGN,  # Use TextChoices
                'description': 'This is a test description',
                'image': image,
                'listing_type': 'Offer',
                'duration': '2',
                'tags': [self.tag1.id, self.tag2.id],
            })


        # Send 10 requests in quick succession
        for i in range(10):
            response = self.client.post(reverse('create_listing'), datas[i])
        
        # Verify that the last request was rate-limited
        self.assertEqual(response.status_code, 429)
        self.assertIn('error', response.json())
        self.assertEqual(response.json()['error'], 'You are creating services too quickly.')
        Listing.objects.all().delete()
        
        
    @override_settings(DISABLE_RATE_LIMIT_CHECK=True)
    def test_create_listing_with_same_title(self):
        # Prepare a valid request payload
        image = SimpleUploadedFile("test_image.jpg", b"file_content", content_type="image/jpeg")
        data = {
            'title': 'Test Listing with same title',
            'category': Category.GRAPHICS_DESIGN,  # Use TextChoices
            'description': 'This is a test description',
            'image': image,
            'listing_type': 'Offer',
            'duration': '2',
            'tags': [self.tag1.id, self.tag2.id],
        }

        response = self.client.post(reverse('create_listing'), data)
        
        # Verify that listing was created successfully
        self.assertEqual(response.status_code, 201)
        
        # Try to create another listing with the same title
        response = self.client.post(reverse('create_listing'), data)
        
        # Verify that the second request failed
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
        self.assertEqual(response.json()['error'], 'You are trying to create a service with duplicated title.')
        Listing.objects.all().delete()
        
    
    @override_settings(DISABLE_RATE_LIMIT_CHECK=True)
    def test_create_listing_with_too_many_listings(self):
        # remove all old listings
        Listing.objects.all().delete()
        image = SimpleUploadedFile("test_image.jpg", b"file_content", content_type="image/jpeg")
        datas = []
        used_titles = []
        for i in range(301):
            titles = 'Test Listing with too many listings' + str(random.randint(1, 1000000))
            while titles in used_titles:
                titles = 'Test Listing with too many listings' + str(random.randint(1, 1000000))
            used_titles.append(titles)
            datas.append({
                'title': titles,
                'category': Category.GRAPHICS_DESIGN,  # Use TextChoices
                'description': 'This is a test description',
                'listing_type': 'Offer',
                'duration': '2',
                'tags': [self.tag1.id, self.tag2.id],
                'image': image,
            })
            
        for i in range(300):
            response = self.client.post(reverse('create_listing'), datas[i])
            self.assertEqual(response.status_code, 201)
            
            
        # Try to create another listing
        response = self.client.post(reverse('create_listing'), datas[300])
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
        self.assertEqual(response.json()['error'], 'You have reached the maximum number of services.')
        Listing.objects.all().delete()
        
        
    
        