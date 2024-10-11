from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.auth.forms import *
from django.contrib.auth import authenticate, login
from django.core.mail import send_mail
import uuid
from .models import Listing, User, ListingResponse, ListingAvailability
from .forms import RegisterForm
from django.contrib.auth import get_user_model
import random
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

    if request.GET.get('new_account', '') == 'true':
        context['new_account'] = True

    return render(request, "index.html", context)


User = get_user_model()

def verify_account_code(request):
    if request.method == 'POST':
        code = request.POST.get('code')
        stored_code = request.session.get('verification_code')

        if code == str(stored_code):
            # Retrieve the stored user data
            user_data = request.session.get('user_data')
            
            if user_data:
                # Create a new user with the saved data
                user = User.objects.create(
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password1'],
                    is_active=True,
                    is_verified=True
                )
                user.set_password(user_data['password1'])  # Set the password correctly
                user.save()

                # Clear session data after successful verification
                del request.session['user_data']
                del request.session['verification_code']

                return redirect('login')  # Redirect to login page after verification
        else:
            return render(request, 'verification_failed.html')  # If code is incorrect
    
    return render(request, 'verify_account_code.html')


def create_account(request):
    if request.method == 'GET':
        form = RegisterForm()
        return render(request, 'create-account.html', {'form': form})
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            # Temporarily store user data in session until verification is completed
            request.session['user_data'] = form.cleaned_data
            verification_code = random.randint(100000, 999999)  # Generate 6-digit code
            request.session['verification_code'] = verification_code

            # Send the six-digit code via email
            send_mail(
                'Verify your account',
                f'Your verification code is: {verification_code}',
                'timebartersystem@gmail.com',  # Use your verified sender email
                [form.cleaned_data['email']],
                fail_silently=False,
            )

            return redirect('verify_account_code')  # Redirect to verification code entry
        else:
            return render(request, 'create-account.html', {'form': form})

def custom_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_verified:
                login(request, user)
                return redirect('home')
            else:
                return render(request, 'login.html', {'error': 'Please verify your email before logging in.'})
        else:
            return render(request, 'login.html', {'error': 'Invalid username or password.'})
    return render(request, 'login.html')


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
