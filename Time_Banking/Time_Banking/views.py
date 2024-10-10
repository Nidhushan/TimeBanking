from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Listing, User, ListingResponse, ListingAvailability
import json

from django.views.decorators.csrf import csrf_exempt


def home(request):
    listings = Listing.objects.all()
    programming_listings = Listing.objects.filter(category='TECH')
    digitalm_listings = Listing.objects.filter(category='MARKETING')
    writing_listings = Listing.objects.filter(category='WRITING')
    business_listings = Listing.objects.filter(category='BUSINESS')

    context = {
        "listings": listings,
        'programming_listings': programming_listings,
        'writing_listings': writing_listings,
        'business_listings': business_listings,
        'digitalm_listings': digitalm_listings,
    }
    return render(request, "index.html", context)

def create_account(request):
    return render(request, 'create-account.html')

def login(request):
    return render(request, 'login.html')

@csrf_exempt  # We disable CSRF for simplicity
def create_user(request):
    # Authurization is needed in the future
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            username = data.get("username")
            password_hash = data.get("password_hash")  # hash by frontend
            multiplier = data.get("multiplier", 1.0)  # Default to 1.0 if not provided
            avg_rating = data.get("avg_rating", 0)  # Default to 0 if not provided

            user = User.objects.create(
                username=username,
                password_hash=password_hash,
                multiplier=multiplier,
                avg_rating=avg_rating,
            )
            user.save()

            # Respond with the newly created user's information to confirm the creation
            return JsonResponse(
                {
                    "id": user.id,
                    "username": user.username,
                    "multiplier": user.multiplier,
                    "avg_rating": float(user.avg_rating),
                },
                status=201,
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    else:
        return JsonResponse({"error": "POST request required"}, status=405)


def user_detail(request, id):
    user = get_object_or_404(User, pk=id)

    # for demo purpose
    data = {
        "username": user.username,
        "multiplier": user.multiplier,
        "avg_rating": float(user.avg_rating),
    }
    return JsonResponse(data)


def get_all_listings(request):
    # for demo purpose
    listings = Listing.objects.all()
    data = []
    for listing in listings:
        data.append(
            {
                "id": listing.id,
                "title": listing.title,
                "category": listing.category,
                "description": listing.description,
                "image": listing.image.url if listing.image else None,
            }
        )
    return JsonResponse(data, safe=False)


def get_responses_for_listing(request, listing_id):
    # for demo purpose
    listing = Listing.objects.get(id=listing_id)
    responses = ListingResponse.objects.filter(listing=listing)
    data = []
    for response in responses:
        data.append(
            {
                "user": response.user.username,
                "message": response.message,
                "status": response.status,
            }
        )
    return JsonResponse(data, safe=False)


def get_availability_for_listing(request, listing_id):
    # for demo purpose
    listing = Listing.objects.get(id=listing_id)
    availabilities = ListingAvailability.objects.filter(listing=listing)
    data = []
    for availability in availabilities:
        data.append(
            {"from_time": availability.from_time, "to_time": availability.to_time}
        )
    return JsonResponse(data, safe=False)
