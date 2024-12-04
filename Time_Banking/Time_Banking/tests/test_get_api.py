from django.test import TestCase
from django.urls import reverse
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from ..models import Tag, Category  # Replace `myapp` with your app name

class APITestCase(TestCase):
    def setUp(self):
        # Create some test tags
        Tag.objects.create(name="Tag1")
        Tag.objects.create(name="Tag2")
        
        # Define URLs
        self.get_categories_url = reverse('get_categories')  
        self.get_tags_url = reverse('get_tags')  

    def test_get_categories(self):
        response = self.client.get(self.get_categories_url)
        
        # Assert the response status code
        self.assertEqual(response.status_code, 200)
        
        # Assert the response data
        categories = [{'id': choice.value, 'name': choice.label} for choice in Category]
        self.assertJSONEqual(response.content, categories)

    def test_get_tags(self):
        response = self.client.get(self.get_tags_url)
        
        # Assert the response status code
        self.assertEqual(response.status_code, 200)
        
        # Assert the response data
        tags = Tag.objects.all()
        expected_tags = [{'id': tag.id, 'name': tag.name} for tag in tags]
        self.assertJSONEqual(response.content, expected_tags)
