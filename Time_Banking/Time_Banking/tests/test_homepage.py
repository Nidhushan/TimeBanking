from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import Q
from ..models import Listing, User

class HomeViewTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Create a user for the listings to have a valid creator.
        self.user = User.objects.create_user(username='testuser', password='testpass')
        image = SimpleUploadedFile("test_image.jpg", b"file_content", content_type="image/jpeg")
        
        # Now create listings with a creator
        Listing.objects.create(
            title="Python Basics",
            description="Learn Python",
            category="TECH",
            creator=self.user,
            image=image
        )
        Listing.objects.create(
            title="Advanced Django",
            description="Django Framework",
            category="TECH",
            creator=self.user,
            image=image
        )
        Listing.objects.create(
            title="Creative Writing",
            description="Short stories",
            category="WRITING",
            creator=self.user,
            image=image
        )
        Listing.objects.create(
            title="Business 101",
            description="Intro to business",
            category="BUSINESS",
            creator=self.user,
            image=image
        )
        Listing.objects.create(
            title="Digital Marketing 101",
            description="SEO and Ads",
            category="MARKETING",
            creator=self.user,
            image=image
        )
        
        
        
    def test_home_view_no_search(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "index.html")

        # Check context keys
        self.assertIn('listings', response.context)
        self.assertIn('programming_listings', response.context)
        self.assertIn('writing_listings', response.context)
        self.assertIn('business_listings', response.context)
        self.assertIn('digitalm_listings', response.context)
        self.assertIn('query', response.context)

        # Check that listings are correctly categorized
        self.assertEqual(response.context['programming_listings'].count(), 2)   
        self.assertEqual(response.context['writing_listings'].count(), 1)
        self.assertEqual(response.context['business_listings'].count(), 1)
        self.assertEqual(response.context['digitalm_listings'].count(), 1)

        # Since no search was done, 'query' should be empty string
        self.assertEqual(response.context['query'], '')

    def test_home_view_with_search(self):
        # Search for 'Django' which should return the "Advanced Django" listing
        response = self.client.get(reverse('home'), {'search': 'Django'})
        self.assertEqual(response.status_code, 200)

        # "Advanced Django" in TECH category should be returned
        listings = response.context['listings']
        self.assertEqual(listings.count(), 1)
        self.assertEqual(listings.first().title, "Advanced Django")

        # Ensure query is set in context
        self.assertEqual(response.context['query'], 'Django')

    def test_home_view_new_account(self):
        # If `new_account=true` in GET params, `new_account` should be True in context
        response = self.client.get(reverse('home'), {'new_account': 'true'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['new_account'])
