from django.shortcuts import render
from .models import Listing

def home(request):
    listings = Listing.objects.all()

    context = {
        'listings': listings,
    }
    return render(request, 'index.html', context)