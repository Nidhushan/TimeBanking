from datetime import timezone
from django.db import models
import datetime
from django.contrib.auth.models import AbstractUser

LISTING_TYPES = [
    (True, "Offer"),
    (False, "Request")
]

# defines top-most category for offers & requests
# class Category(models.Model):
#     name = models.CharField(max_length=200)
#     def __str__(self):
#         return self.name

# Use enum (since we have pre-defined categories)
class Category(models.TextChoices):
    GRAPHICS_DESIGN = 'GRAPHICS', 'Graphics & Design'
    PROGRAMMING_TECH = 'TECH', 'Programming & Tech'
    DIGITAL_MARKETING = 'MARKETING', 'Digital Marketing'
    VIDEO_ANIMATION = 'VIDEO', 'Video & Animation'
    WRITING_TRANSLATION = 'WRITING', 'Writing & Translation'
    MUSIC_AUDIO = 'MUSIC', 'Music & Audio'
    BUSINESS = 'BUSINESS', 'Business'
    FINANCE = 'FINANCE', 'Finance'
    AI_SERVICES = 'AI', 'AI Services'
    PERSONAL_GROWTH = 'GROWTH', 'Personal Growth'

# tags within a category
class Tag(models.Model):
    category = models.CharField(max_length=20, choices=Category.choices) # enum for Category
    name = models.CharField(max_length=200)
    def __str__(self):
        return self.name
    

# user account
class User(AbstractUser):
    multiplier = models.FloatField(default=1.0) # or DecimalField?
    avg_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00) # 1.00 to 5.00, or 0.00
    is_verified = models.BooleanField(default=False)  # Track if user is verified
    verification_code = models.CharField(max_length=100, blank=True, null=True)  # Store verification code
    # TODO: profiles
    name = models.CharField(max_length=100)
    picture = models.ImageField(upload_to='static/images/user')
    title = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    bio = models.TextField(blank=True)  # optional
    link = models.URLField(blank=True)  # optional
    def __str__(self):
        return self.username

# parent class of BOTH offers AND requests
class Listing(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(max_length=20, choices=Category.choices) # enum for Category
    tags = models.ManyToManyField(Tag) # backend needs to check that tags belong to category
    title = models.CharField(max_length=50) # use CharField (adjust length as needed)
    description = models.TextField(max_length=1000) # bound to 1000 characters (adjust as needed)
    image = models.ImageField(upload_to='static/images/listing')
    listing_type = models.BooleanField(choices=LISTING_TYPES)
    duration = models.DurationField() # how long the work is expected/preferred to take
    posted_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.title

# simple model for Week 5 demo
# class Listing(models.Model):
#     title = models.CharField(max_length=255) # use CharField
#     category = models.CharField(max_length=20, choices=Category.choices) # enum for Category
#     image = models.ImageField(upload_to='static/images/listing')
#     description = models.TextField()
#     def __str__(self):
#         return self.title

# someone responds to an offer or a request
class ListingResponse(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField() # initial message
    status = models.SmallIntegerField() # TODO: map integers to types, eg. 1 = accept, 2 = reject, etc.

# availabilities of a listing
class ListingAvailability(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    from_time = models.DateTimeField()
    to_time = models.DateTimeField()

# images within a listing
# class ListingImage(models.Model):
#     listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
#     url = models.URLField()
#     # TODO: other fields for implementation convenience?
