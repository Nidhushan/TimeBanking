from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.forms import *
from .models import Listing, User, ListingResponse, ListingAvailability
from .forms import RegisterForm
import json

def home(request):
    listings = Listing.objects.all()
    programming_listings = Listing.objects.filter(category='TECH')
    writing_listings = Listing.objects.filter(category='WRITING')
    business_listings = Listing.objects.filter(category='BUSINESS')
    digitalm_listings = Listing.objects.filter(category='MARKETING')

    context = {
        "listings": listings,
        'programming_listings': programming_listings,
        'writing_listings': writing_listings,
        'business_listings': business_listings,
        'digitalm_listings': digitalm_listings,
    }
    return render(request, "index.html", context)

def create_account(request):
    if request.method == 'GET':
        form = RegisterForm()
        return render(request, 'create-account.html', {'form': form})   
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            return redirect('/') # TODO: what happens after someone has logged in?
        else:
            form = RegisterForm()
            return render(request, 'create-account.html', {'form': form})


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
