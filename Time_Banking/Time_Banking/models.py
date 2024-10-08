from datetime import timezone
from django.db import models
import datetime

LISTING_TYPES = [
    (True, "Offer"),
    (False, "Request")
]

# defines top-most category for offers & requests
class Category(models.Model):
    name = models.CharField(max_length=200)
    def __str__(self):
        return self.name

# tags within a category
class Tag(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    def __str__(self):
        return self.name

# user account
class User(models.Model):
    username = models.CharField(max_length=200) # this limit needs to be in the frontend
    password_hash = models.TextField()
    multiplier = models.FloatField(default=1.0) # or DecimalField?
    avg_rating = models.DecimalField(max_digits=3, decimal_places=2) # 1.00 to 5.00
    # TODO: profiles
    def __str__(self):
        return self.username

# parent class of BOTH offers AND requests
class Listing(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category)
    tags = models.ManyToManyField(Tag) # backend needs to check that tags belong to category
    title = models.TextField() # or CharField?
    description = models.TextField()
    listing_type = models.BooleanField(choices=LISTING_TYPES)
    duration = models.DurationField() # how long the work is expected/preferred to take
    posted_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.title

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
class ListingImage(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    url = models.URLField()
    # TODO: other fields for implementation convenience?
