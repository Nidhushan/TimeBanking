from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.auth.forms import *
from django.contrib.auth import authenticate, login
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
import uuid
from .models import Listing, User, ListingResponse, ListingAvailability
from .forms import RegisterForm, ProfileCreationForm
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
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
            return render(request, 'registration/verification_failed.html')  # If code is incorrect
    
    return render(request, 'registration/verify_account_code.html')

def resend_verification_email(request):
    # Check if user data exists in the session
    user_data = request.session.get('user_data')
    
    if user_data:
        verification_code = random.randint(100000, 999999)  # Generate a new 6-digit code
        request.session['verification_code'] = verification_code

        # Send the verification code via email
        send_mail(
            'Verify your account',
            f'Your new verification code is: {verification_code}',
            'timebartersystem@gmail.com',
            [user_data['email']],
            fail_silently=False,
        )

        # Redirect to the verification page
        return redirect('verify_account_code')
    else:
        return redirect('create_account')  # If user data doesn't exist, redirect to account creation

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


"""
curl -X POST http://localhost:8000/api/change-password/ \
     -H "Content-Type: application/json" \
     -d '{"username": "testuser", "current_password": "oldpassword", "new_password": "newpassword"}'

"""
@login_required  # Ensures the user is logged in
def change_password(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            current_password = data.get('current_password')
            new_password = data.get('new_password')

            user = User.objects.get(username=username)

            # Check if the current password is correct
            if not user.check_password(current_password):
                return JsonResponse({'error': 'Current password is incorrect'}, status=400)
            
            try:
                validate_password(new_password, user=user)
            except ValidationError as e:
                return JsonResponse({'error': list(e.messages)}, status=400)

            # Set the new password
            user.set_password(new_password)
            user.save()

            return JsonResponse({'status': 'Password changed successfully'}, status=200)

        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
        except KeyError:
            return JsonResponse({'error': 'Invalid input, missing fields'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'POST request required'}, status=405)


@login_required  # Ensures the user is logged in
def change_password_page(request):
    return render(request, 'change_password.html')


"""
curl -X POST http://localhost:8000/api/delete-account/ \
     -b "sessionid=<your_session_id>"
"""
@login_required  # Ensures the user is logged in
@csrf_exempt  
def delete_account(request):
    if request.method == 'POST':
        try:
            # Get the logged-in user
            user = request.user

            # Delete the user's account
            user.delete()

            return JsonResponse({'status': 'Account deleted successfully'}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'POST request required'}, status=405)


@login_required  # Make sure the user is logged in to access this page
def delete_account_page(request):
    return render(request, 'delete_account.html')


@login_required   # Ensures the user is logged in
# @csrf_exempt  # For handling form submissions via AJAX, use CSRF protection in production
def update_user_settings(request):
    if request.method == 'POST':
        try:
            user = request.user 

            # Get the updated fields from the form or JSON data
            name = request.POST.get('name')
            title = request.POST.get('title')
            location = request.POST.get('location')
            bio = request.POST.get('bio')
            link = request.POST.get('link')
            picture = request.FILES.get('picture')  

            # Update user information only for the fields that are provided
            if name is not None:
                user.name = name
            if title is not None:
                user.title = title
            if location is not None:
                user.location = location
            if bio is not None:
                user.bio = bio
            if link is not None:
                user.link = link
            if picture is not None:
                user.picture = picture  
            user.save()

            return JsonResponse({'status': 'Profile updated successfully'}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'POST request required'}, status=405)


@login_required   # Ensures the user is logged in
def user_settings_page(request):
    return render(request, 'user_settings.html')


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

def get_listing_by_id(request, listing_id):
    listing = Listing.objects.get(id=listing_id)
    data = {
        "id": listing.id,
        "title": listing.title,
        "category": listing.category,
        "description": listing.description,
        "image": listing.image.url if listing.image else None,
    }
    return JsonResponse(data)


def get_responses_for_listing(request, listing_id):
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
    listing = Listing.objects.get(id=listing_id)
    availabilities = ListingAvailability.objects.filter(listing=listing)
    data = []
    for availability in availabilities:
        data.append(
            {"from_time": availability.from_time, "to_time": availability.to_time}
        )
    return JsonResponse(data, safe=False)


@login_required  # Ensures the user must be logged in
def create_listing(request):
    if request.method == 'POST':
        try:
            title = request.POST.get('title')
            category = request.POST.get('category')
            description = request.POST.get('description')
            image = request.FILES.get('image') # We can only have 1 image per listing by now

            # Ensure all required fields are provided
            if not title or not category or not description or not image:
                return JsonResponse({'error': 'Missing required fields'}, status=400)

            # Create the listing (user is associated with the request.user)
            listing = Listing.objects.create(
                # creator=request.user,
                title=title,
                category=category,
                description=description,
                image=image
            )
            listing.save()

            return JsonResponse({
                'id': listing.id,
                'title': listing.title,
                'category': listing.category,
                'description': listing.description,
                'image_url': listing.image.url
            }, status=201)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'POST request required'}, status=405)


def create_profile(request):
    if request.method=='POST':
        form = ProfileCreationForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return JsonResponse({"status": "success", "message": "Profile created successfully"})
        else:
            return JsonResponse({"status": "error", "errors": form.errors}, status=400)
    else:
        form = ProfileCreationForm(instance=request.user)
        return render(request, 'create_profile.html', {'form': form})  # pre-fill the form with current user data
    # render frontend
 
