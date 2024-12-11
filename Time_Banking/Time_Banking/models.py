
from datetime import timezone, timedelta
from django.db import models
import datetime
from django.contrib.auth.models import AbstractUser
from datetime import timedelta
from django.core.exceptions import ValidationError

LISTING_TYPES = [
    (True, "Offer"),
    (False, "Request")
]

STATUS_CHOICES = [
    ("Available", "Available"),
    ("In Progress", "In Progress"),
    ("Completed", "Completed"),
    ("Fulfilled", "Fulfilled"),
    ("Closed", "Closed"),
]
STATUS_CHOICES_OFFER = ["Available", "In Progress", "Completed"]
STATUS_CHOICES_REQUEST = ["Available", "Fulfilled", "Closed"]

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
    
class Skill(models.Model):
    
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
# user account
class User(AbstractUser):
    multiplier = models.FloatField(default=1.0)
    avg_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_minutes = models.FloatField(default=0.0) 
    is_verified = models.BooleanField(default=False)  # Track if user is verified
    verification_code = models.CharField(max_length=100, blank=True, null=True)  # Store verification code
    # TODO: profiles
    name = models.CharField(max_length=100)
    picture = models.ImageField(upload_to='static/images/user', blank=True)
    title = models.CharField(max_length=100,blank=True)
    location = models.CharField(max_length=100,blank=True)
    bio = models.TextField(blank=True)  # optional
    link = models.URLField(blank=True)  # optional
    skills = models.ManyToManyField(Skill, blank=True)
    def __str__(self):
        return self.username

# parent class of BOTH offers AND requests
class Listing(models.Model):
    LISTING_TYPES = [
        ("Offer", "Offer"),
        ("Request", "Request")
    ]
    creator = models.ForeignKey(User, related_name="services", on_delete=models.CASCADE)
    category = models.CharField(max_length=20, choices=Category.choices) # enum for Category
    tags = models.ManyToManyField(Tag) # backend needs to check that tags belong to category
    title = models.CharField(max_length=50) # use CharField (adjust length as needed)
    description = models.TextField(max_length=1000) # bound to 1000 characters (adjust as needed)
    image = models.ImageField(upload_to='static/images/listing')
    listing_type = models.CharField(max_length=10, choices=LISTING_TYPES, null=True)
    duration = models.DurationField(default=timedelta(hours=1)) # how long the work is expected/preferred to take
    posted_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Available")

    def clean(self):
        valid_statuses = STATUS_CHOICES_OFFER if self.listing_type else STATUS_CHOICES_REQUEST
        if self.status and self.status not in valid_statuses:
            listing_type_label = "Offer" if self.listing_type else "Request"
            raise ValidationError({
                'status': f"Invalid status for {listing_type_label}. Valid options are: {', '.join(valid_statuses)}"
            })
        
    def save(self, *args, **kwargs):
        # If already exists and is being edited, reset its status
        if self.pk:
            self.status = "Available"
        super().save(*args, **kwargs)

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

# New model for service transactions
# models.py

class ServiceTransaction(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='provided_transactions')
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requested_transactions')
    duration = models.IntegerField()  # Duration in minutes
    feedback_given = models.BooleanField(default=False)
    multiplier = models.FloatField(default=1.0)
    status = models.CharField(
        max_length=20,
        choices=[
            ('Pending', 'Pending'),
            ('Completed', 'Completed'),
            ('Cancelled', 'Cancelled'),
        ],
        default='Pending'
    )

    def calculate_credits(self):
        return round(self.duration * self.multiplier / 60, 2)
    
# New model for feedback
class Feedback(models.Model):
    transaction = models.OneToOneField(ServiceTransaction, on_delete=models.CASCADE)
    provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedback_received')
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedback_given')
    rating = models.IntegerField()
    comment = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Feedback for Transaction {self.transaction.id} by {self.requester}"

# models.py

def update_provider_metrics(transaction):
    provider = transaction.provider

    # Update average rating
    all_ratings = Feedback.objects.filter(provider=provider).values_list('rating', flat=True)
    avg_rating = sum(all_ratings) / len(all_ratings) if all_ratings else 0

    # Update multiplier
    multiplier = 1 + (avg_rating - 3) * 0.1
    provider.multiplier = max(0.5, min(2.0, multiplier))

    # Update total credits
    earned_credits = ServiceTransaction.objects.filter(
        provider=provider, status='Completed'
    ).aggregate(
        total_credits=Sum(models.F('duration') * models.F('multiplier') / 60)
    )['total_credits'] or 0

    provider.total_minutes = earned_credits * 60
    provider.avg_rating = round(avg_rating, 2)
    provider.save()

# images within a listing
# class ListingImage(models.Model):
#     listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
#     url = models.URLField()
#     # TODO: other fields for implementation convenience?


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    url = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Notification for {self.user.username} - {self.message[:20]}"