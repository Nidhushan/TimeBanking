from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.db import models
from django.db.models import Q
from django.http import JsonResponse, HttpResponseRedirect, HttpResponseNotAllowed
from django.contrib.auth.forms import *
from django.contrib.auth import authenticate, login
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings
import uuid
from .models import Listing, User, ListingResponse, ListingAvailability, Category, Tag, Skill, Notification, Feedback, ServiceTransaction, update_provider_metrics
from .forms import RegisterForm, ProfileCreationForm, ProfileEditForm, AddSkillForm
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import random
import json
from .forms import ProfileEditForm
from django.contrib import messages
from django.utils.timezone import localtime
from django.http import HttpResponseForbidden


@login_required
@csrf_exempt
def mark_listing_completed(request, listing_id):
    try:
        listing = get_object_or_404(Listing, id=listing_id, creator=request.user)

        if listing.status == "Completed":
            return JsonResponse({'error': 'Listing already marked as completed.'}, status=400)

        # Find the accepted response
        accepted_response = ListingResponse.objects.filter(listing=listing, status=2).first()
        if not accepted_response:
            return JsonResponse({'error': 'No accepted applicant found.'}, status=400)

        # Mark the listing as completed
        listing.status = "Completed"
        listing.save()

        # Create or update service transaction
        transaction, created = ServiceTransaction.objects.get_or_create(
            listing=listing,
            provider=accepted_response.user,
            requester=listing.creator if listing.listing_type == "Request" else accepted_response.user,
            defaults={
                'duration': listing.duration.total_seconds() / 60,
                'status': 'Completed',
            }
        )

        # Notify the applicant
        Notification.objects.create(
            user=accepted_response.user,
            message=f"Your service '{listing.title}' was marked as completed! Submit your feedback.",
            url=f"/submit-feedback/{listing.id}/"
        )

        return JsonResponse({'success': 'Listing marked as completed.'}, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@csrf_exempt
def view_applicants(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    responses = ListingResponse.objects.filter(listing=listing)
    
    # Check if service is already accepted
    if ServiceTransaction.objects.filter(listing=listing, status='Pending').exists():
        transaction = ServiceTransaction.objects.get(listing=listing, status='Pending')
        return render(request, 'view_applicants.html', {'transaction': transaction})

    if request.method == 'POST':
        response_id = request.POST.get('response_id')
        selected_response = get_object_or_404(ListingResponse, id=response_id)

        # Create the service transaction
        transaction = ServiceTransaction.objects.create(
            listing=listing,
            provider=listing.creator,
            requester=selected_response.user,
            duration=listing.duration,
            status='Pending'
        )

        # Notify the requester
        Notification.objects.create(
            user=selected_response.user,
            message="Your service has been accepted!",
            url="/accepted-services/"
        )

        # Update Response Statuses
        selected_response.status = 2  # Accepted
        selected_response.message = "Accepted"
        selected_response.save()

        # Mark other responses as Rejected
        for response in responses.exclude(id=response_id):
            response.status = 3  # Rejected
            response.message = "Rejected"
            response.save()
            Notification.objects.create(
                user=response.user,
                message="Your application was rejected.",
                url="/services"
            )

        return redirect('view_applicants', listing_id=listing.id)

    return render(request, 'view_applicants.html', {'responses': responses})


@login_required
def accepted_services(request):
    transactions = ServiceTransaction.objects.filter(
        requester=request.user, 
        status='Pending',
        feedback_given=False
    )
    return render(request, 'accepted_services.html', {'transactions': transactions})


from django.db.models import Sum

def calculate_quality_multiplier(rating):
    return {
        5: 1.5,
        4: 1.2,
        3: 1.0,
        2: 0.8,
        1: 0.5
    }.get(rating, 1.0)

@login_required
def submit_feedback(request, listing_id):
    try:
        # Fetch the transaction related to the listing
        transaction = get_object_or_404(
            ServiceTransaction,
            listing_id=listing_id,
            requester=request.user,  # The one submitting feedback
            status='Completed',
            feedback_given=False
        )

        provider = transaction.provider  # Correct provider receiving feedback

        if request.method == 'POST':
            # Collect ratings from form submission
            q1 = int(request.POST.get('q1'))
            q2 = int(request.POST.get('q2'))
            q3 = int(request.POST.get('q3'))
            q4 = int(request.POST.get('q4'))

            # Calculate average rating
            avg_rating = round((q1 + q2 + q3 + q4) / 4)

            # Create feedback entry
            Feedback.objects.create(
                transaction=transaction,
                provider=provider,  # Feedback goes to the provider
                requester=request.user,  # Person submitting feedback
                rating=avg_rating,
                comment=f"Q1: {q1}, Q2: {q2}, Q3: {q3}, Q4: {q4}",
                details=request.POST.get('review')
            )

            # Mark the transaction as having received feedback
            transaction.feedback_given = True
            transaction.save()

            # Update metrics for the provider
            update_provider_metrics(provider, transaction.listing_id)

            messages.success(request, "Feedback submitted successfully!")
            return redirect("home")

        return render(request, "submit_feedback.html", {'transaction': transaction})

    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect("home")


def home(request):
    listings = Listing.objects.all()
    programming_listings = Listing.objects.filter(category='TECH')
    writing_listings = Listing.objects.filter(category='WRITING')
    business_listings = Listing.objects.filter(category='BUSINESS')
    digitalm_listings = Listing.objects.filter(category='MARKETING')

    # Handle search
    query = request.GET.get('search', '')  # Capture the search query from the URL
    sort_option = request.GET.get('sort', 'date')
    sort_order = request.GET.get('order', 'asc')
    selected_category = request.GET.get('category', '')  # Get selected category from URL parameter

    listings = Listing.objects.filter(title__icontains=query)

    # Filter by selected category, if provided
    if selected_category:
        listings = listings.filter(category=selected_category)

    # Sort based on the selected option
    if sort_option == 'date':
        listings = listings.order_by('posted_at' if sort_order == 'asc' else '-posted_at')
    elif sort_option == 'cost':
        listings = listings.order_by('duration' if sort_order == 'asc' else '-duration')
    elif sort_option == 'category':
        listings = listings.order_by('category' if sort_order == 'asc' else '-category')

    # Fetch all categories for dropdown
    categories = Category.choices

    if query:
        listings = listings.filter(
            Q(title__icontains=query) |  # Search in the title
            Q(description__icontains=query)  # Search in the description
        )

    context = {
        "listings": listings,
        'programming_listings': programming_listings,
        'writing_listings': writing_listings,
        'business_listings': business_listings,
        'digitalm_listings': digitalm_listings,
        'query': query if query else '',
        'sort_option': sort_option,
        'sort_order': sort_order,
        'selected_category': selected_category,
        'categories': categories,
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
            user_data = request.session.get('user_data')
            if user_data:
                user = User.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password1'],
                    is_active=True,
                    is_verified=True
                )
                del request.session['user_data']
                del request.session['verification_code']
                login(request, user)
                return redirect('edit_profile')
        else:
            return render(request, 'registration/verification_failed.html')
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
    
def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()

        if user:
            reset_code = random.randint(100000, 999999)
            request.session['reset_code'] = reset_code
            request.session['reset_email'] = email

            # Send the code via email
            send_mail(
                'Password Reset Code',
                f'Your password reset code is: {reset_code}',
                'timebartersystem@gmail.com',  # Replace with your email
                [email],
                fail_silently=False,
            )

            return redirect('verify_reset_code')  # Redirect to code verification page
        else:
            return render(request, 'registration/forgot_password.html', {'error': 'Email not found.'})

    return render(request, 'registration/forgot_password.html')

def verify_reset_code(request):
    if request.method == 'POST':
        entered_code = request.POST.get('code')
        stored_code = request.session.get('reset_code')

        if entered_code == str(stored_code):
            return redirect('reset_password')  # Redirect to reset password form
        else:
            return render(request, 'registration/verify_reset_code.html', {'error': 'Invalid code.'})

    return render(request, 'registration/verify_reset_code.html')

def reset_password(request):
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password == confirm_password:
            email = request.session.get('reset_email')
            user = User.objects.filter(email=email).first()

            if user:
                try:
                    validate_password(new_password, user=user)  # Validate password strength
                    user.set_password(new_password)
                    user.save()

                    # Clear session data
                    del request.session['reset_email']
                    del request.session['reset_code']

                    return redirect('login')
                except ValidationError as e:
                    return render(request, 'registration/reset_password.html', {'error': list(e.messages)})

        return render(request, 'registration/reset_password.html', {'error': 'Passwords do not match.'})

    return render(request, 'registration/reset_password.html')

def create_account(request):
    if request.method == 'GET':
        form = RegisterForm()
        return render(request, 'create-account.html', {'form': form})
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            # Check if the email already exists
            email = form.cleaned_data.get('email')
            if User.objects.filter(email=email).exists():
                return render(request, 'create-account.html', {'error': 'An account with this email already exists.'})

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
                if not user.name or not user.title or not user.location:
                    return redirect('edit_profile')
                return redirect('home')
            else:
                return render(request, 'registration/login.html', {'error': 'Please verify your email before logging in.'})
        else:
            return render(request, 'registration/login.html', {'error': 'Invalid username or password.'})
    return render(request, 'registration/login.html')


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
            confirm_password = data.get('confirm_password')
            
            if not username or not current_password or not new_password or not confirm_password:
                return JsonResponse({'error': 'Invalid input, missing fields'}, status=400)
            
            if username != request.user.username:
                return JsonResponse({'error': 'Not authorized to change password'}, status=403)
            
            if new_password != confirm_password:
                return JsonResponse({'error': 'New passwords do not match'}, status=400)

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

            return JsonResponse({'status': 'success'}, status=200)


        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'POST request required'}, status=405)


# @login_required  # Ensures the user is logged in
# def change_password_page(request):
#     return render(request, 'user_settings.html')


"""
curl -X POST http://localhost:8000/api/delete-account/ \
     -b "sessionid=<your_session_id>"
"""
# @csrf_exempt  
@login_required  # Ensures the user is logged in
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


# @login_required  # Make sure the user is logged in to access this page
# def delete_account_page(request):
#     return render(request, 'delete_account.html')


# @login_required   # Ensures the user is logged in
# # @csrf_exempt  # For handling form submissions via AJAX, use CSRF protection in production
# def update_user_settings(request):
#     if request.method == 'POST':
#         try:
#             user = request.user 

#             # Get the updated fields from the form or JSON data
#             name = request.POST.get('name')
#             title = request.POST.get('title')
#             location = request.POST.get('location')
#             bio = request.POST.get('bio')
#             link = request.POST.get('link')
#             picture = request.FILES.get('picture')  

#             # Update user information only for the fields that are provided
#             if name is not None:
#                 user.name = name
#             if title is not None:
#                 user.title = title
#             if location is not None:
#                 user.location = location
#             if bio is not None:
#                 user.bio = bio
#             if link is not None:
#                 user.link = link
#             if picture is not None:
#                 user.picture = picture  
#             user.save()

#             return JsonResponse({'status': 'Profile updated successfully'}, status=200)

#         except Exception as e:
#             return JsonResponse({'error': str(e)}, status=500)

#     return JsonResponse({'error': 'POST request required'}, status=405)


@login_required   # Ensures the user is logged in
def user_settings_page(request):
    return render(request, 'user_settings.html')


# def user_detail(request, id):
#     user = get_object_or_404(User, pk=id)
#     data = {
#         "email": user.email,  # Include email
#         "multiplier": user.multiplier,
#         "avg_rating": float(user.avg_rating),
#         "name": user.name,
#         "picture_url": user.picture.url if user.picture else "",
#         "title": user.title,
#         "location": user.location,
#         "bio": user.bio,
#         "link": user.link,
#     }
#     return JsonResponse(data)

def get_all_listings(request):
    # should be modified if the database of listings is too large
    listings = Listing.objects.all()
    
    data = []
    for listing in listings:
        category_id = listing.category
        data.append(
            {
                'id': listing.id,
                'creator': listing.creator.username,  
                'category': Category(category_id).label,  
                'tags': [tag.name for tag in listing.tags.all()], 
                'title': listing.title,
                'description': listing.description,
                'image': listing.image.url if listing.image else None,  
                'listing_type': listing.listing_type, 
                'duration': str(listing.duration),  
                'posted_at': listing.posted_at.strftime('%Y-%m-%d %H:%M:%S'),  
                'edited_at': listing.edited_at.strftime('%Y-%m-%d %H:%M:%S'),  
            }
        )
    return JsonResponse(data, safe=False)


# def get_listing_by_id(request, listing_id):
#     try:
#         # Fetch the listing by ID
#         listing = get_object_or_404(Listing, id=listing_id)
#         category_id = listing.category
        
#         data = {
#             'id': listing.id,
#             'creator': listing.creator.username,  
#             'category': Category(category_id).label,  
#             'tags': [tag.name for tag in listing.tags.all()], 
#             'title': listing.title,
#             'description': listing.description,
#             'image': listing.image.url if listing.image else None, 
#             'listing_type': listing.listing_type, 
#             'duration': str(listing.duration), 
#             'posted_at': listing.posted_at.strftime('%Y-%m-%d %H:%M:%S'),  
#             'edited_at': listing.edited_at.strftime('%Y-%m-%d %H:%M:%S'), 
#         }
#         return JsonResponse(data, status=200)
    
#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=500)


# def get_responses_for_listing(request, listing_id):
#     listing = Listing.objects.get(id=listing_id)
#     responses = ListingResponse.objects.filter(listing=listing)
#     data = []
#     for response in responses:
#         data.append(
#             {
#                 "user": response.user.username,
#                 "message": response.message,
#                 "status": response.status,
#             }
#         )
#     return JsonResponse(data, safe=False)


# def get_availability_for_listing(request, listing_id):
#     listing = Listing.objects.get(id=listing_id)
#     availabilities = ListingAvailability.objects.filter(listing=listing)
#     data = []
#     for availability in availabilities:
#         data.append(
#             {"from_time": availability.from_time, "to_time": availability.to_time}
#         )
#     return JsonResponse(data, safe=False)


def view_listing(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    
    context = {"listing": listing}

    if request.user.is_authenticated:
        context['feedback_given'] = Feedback.objects.filter(
            transaction__listing=listing,
            transaction__requester=request.user
        ).exists()
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])
        context['service_accepted'] = ListingResponse.objects.filter(listing=listing, status=2).exists()
        context['service_completed'] = ServiceTransaction.objects.filter(listing=listing, status='Completed').exists()

        # Check if service has been accepted
        service_accepted = ListingResponse.objects.filter(
            listing=listing, status=2  # 2 = Accepted
        ).exists()
    
    return render(request, 'view_listing.html', context)

    


@csrf_exempt
@login_required
def apply_service(request, listing_id):
    if request.method == 'POST':
        # Retrieve the listing using the ID
        listing = get_object_or_404(Listing, id=listing_id)

        # Check if the listing creator is not the same as the current user
        if listing.creator == request.user:
            return JsonResponse({'error': 'You cannot apply your own service/request.'}, status=403)
        
        # Check for duplicate application
        if ListingResponse.objects.filter(listing=listing, user=request.user).exists():
            return JsonResponse({'error': 'You have already applied to this listing.'}, status=400)

        # Create a response to mark the service/request as accepted
        ListingResponse.objects.create(
            listing=listing,
            user=request.user,
            message="Pending",
            status=1  # You can use an appropriate integer to indicate 'Accepted' status
        )

        Notification.objects.create(
            user=listing.creator,
            message="A new applicant on your service.",
            url="/myservices"
        )

        # Logic to notify the listing creator (for example, by email or in-app notification)
        # Here, we are just simulating a simple success response
        return JsonResponse({'success': 'Service/Request apply successfully!'}, status=200)

    return JsonResponse({'error': 'Only POST requests are allowed.'}, status=405)


# Fetch the categories from the database
def get_categories(request):
    # Fetch categories from the TextChoices enum
    categories = [{'id': choice.value, 'name': choice.label} for choice in Category]
    return JsonResponse(categories, safe=False, status=200)


# Fetch the tags from the database
def get_tags(request):
    tags = Tag.objects.all()
    tag_list = [{'id': tag.id, 'name': tag.name} for tag in tags]
    return JsonResponse(tag_list, safe=False, status=200)

def get_tags_by_category(request, category_id):
    tags = Tag.objects.filter(category=category_id)
    tag_list = [{'id': tag.id, 'name': tag.name} for tag in tags]
    return JsonResponse(tag_list, safe=False, status=200)


"""
curl -X POST http://localhost:8000/api/create-listing/
     -b "sessionid=<your_session_id>" 
     -F 'title=My New Listing' 
     -F 'category=1' 
     -F 'description=This is a new listing description' 
     -F 'listing_type=True' 
     -F 'duration=2' # in hours
     -F 'tags=1' -F 'tags=2'
     -F 'image=@/path/to/image.jpg'
"""
@login_required  # Ensure the user is logged in
def create_listing(request):
    if request.method == 'POST':
        try:
            # Get the form data
            title = request.POST.get('title')
            category_id = request.POST.get('category')  
            description = request.POST.get('description')
            image = request.FILES.get('image')  # We can only have 1 image per listing
            listing_type = request.POST.get('listing_type')  # Expecting 'True' or 'False'
            duration_in_minutes = request.POST.get('duration')  # Expected format: integer (minutes)
            tag_ids = request.POST.getlist('tags')  # Expecting a list of tag IDs

            if not title or not category_id or not description or not image or not listing_type or not duration_in_minutes:
                missing_fields = [field for field in ['title', 'category', 'description', 'image', 'listing_type', 'duration'] if not request.POST.get(field)]
                error_msg = f'Missing required fields: {", ".join(missing_fields)}'
                return JsonResponse({'error': error_msg}, status=400)
            
            if len(description) > 5000:
                return JsonResponse({'error': 'Description is too long'}, status=400)

            if listing_type not in ['Offer', 'Request']:
                return JsonResponse({'error': 'Invalid listing type.'}, status=400)

            category = Category(category_id).label

            try:
                duration_in_minutes = int(duration_in_minutes)  # Ensure it's an integer
                duration = timedelta(minutes=duration_in_minutes)  # Convert to timedelta
            except ValueError:
                return JsonResponse({'error': 'Duration must be a valid integer'}, status=400)
            
        
            
            
            # check listing is valid to create or not
            user_listings_old = Listing.objects.filter(creator=request.user)
            if len(user_listings_old) > 0:
                if len(user_listings_old) > 299:
                    return JsonResponse({'error': 'You have reached the maximum number of services.'}, status=400)
                for user_listing in user_listings_old:
                    if user_listing.title == title:
                        return JsonResponse({'error': 'You are trying to create a service with duplicated title.'}, status=400)
                latest_listing_posted_at = user_listings_old.latest('posted_at').posted_at

            listing = Listing.objects.create(
                creator=request.user,  
                title=title,
                category=category_id,
                description=description,
                image=image,
                listing_type=listing_type,
                duration=duration
            )
            
            # check if the user is creating services too quickly 30 seconds
            if not getattr(settings, 'DISABLE_RATE_LIMIT_CHECK', False): # Disable rate limit check for test cases
                if len(user_listings_old) > 0:
                    if latest_listing_posted_at > listing.posted_at - timedelta(seconds=30):
                        listing.delete()
                        return JsonResponse({'error': 'You are creating services too quickly.'}, status=429)
            
            
            listing.save() # save the listing to the database

            if tag_ids:
                tags = Tag.objects.filter(id__in=tag_ids)
                listing.tags.set(tags)

            return JsonResponse({
                'id': listing.id,
                'title': listing.title,
                'category': category,
                'tags': [tag.name for tag in listing.tags.all()], 
                'description': listing.description,
                'image_url': listing.image.url if listing.image else None,
                'listing_type': listing.listing_type,
                'duration': str(listing.duration)
            }, status=201) # return the created listing

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'POST request required'}, status=405)

@login_required  # Make sure the user is logged in to access this page
def create_listing_page(request):
    return render(request, 'create_listing.html')

"""
curl -X POST "http://localhost:8000/api/edit-listing/1/" \
     -b "sessionid=<sessionid>" \
     -F "title=Updated Listing Title" \
     -F "description=Updated description for the listing" \
     -F "category=TECH" \
     -F "duration=3" \
     -F "status=In Progress" \
     -F "tags=2" -F "tags=3" \
     -F "image=@<image_path>"
"""
# views.py

@login_required
def edit_listing(request, listing_id):
    if request.method == 'POST':
        try:
            listing = get_object_or_404(Listing, id=listing_id)
            # Simulate form validation logic
            # if request.POST['duration'] <= 0:
            #     raise ValidationError("Invalid duration.")
            try:
                duration_in_minutes = int(request.POST.get('duration'))
                if duration_in_minutes <= 0:
                    return JsonResponse({'error': 'Invalid duration.'}, status=400)
            except (ValueError, TypeError):
                return JsonResponse({'error': 'Duration must be a valid integer'}, status=400)
            description = request.POST.get('description')
            if len(description) > 1000:
                return JsonResponse({'error': 'Description is too long'}, status=400)
            # Update the listing logic
        except ValidationError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        try:
            listing = get_object_or_404(Listing, id=listing_id, creator=request.user)

            # Collect form data
            title = request.POST.get('title')
            description = request.POST.get('description')
            category_id = request.POST.get('category')
            duration_in_minutes = request.POST.get('duration')
            listing_type = request.POST.get('listing_type')
            tag_ids = request.POST.getlist('tags')
            image = request.FILES.get('image')

            # Validation checks
            if not all([title, description, category_id, duration_in_minutes, listing_type]):
                missing_fields = [field for field in ['title', 'description', 'category', 'duration', 'listing_type'] if not request.POST.get(field)]
                return JsonResponse({'error': f'Missing required fields: {", ".join(missing_fields)}'}, status=400)
            
            if len(description) > 1000:
                return JsonResponse({'error': 'Description is too long'}, status=400)
            
            if listing_type not in ['Offer', 'Request']:
                return JsonResponse({'error': 'Invalid listing type.'}, status=400)

            # Update listing details
            listing.title = title
            listing.description = description
            listing.category = category_id
            listing.listing_type = listing_type
            listing.duration = timedelta(minutes=int(duration_in_minutes))
            listing.status = "Available"  # Reset status

            if image:
                listing.image = image

            if tag_ids:
                tags = Tag.objects.filter(id__in=tag_ids)
                listing.tags.set(tags)

            listing.save()

            # Reset previous transactions and responses
            ServiceTransaction.objects.filter(listing=listing).delete()
            previous_responses = ListingResponse.objects.filter(listing=listing)
            
            # Notify previous applicants about the reset
            for response in previous_responses:
                Notification.objects.create(
                    user=response.user,
                    message=f"Service '{listing.title}' was updated and reopened. Feel free to apply again!",
                    url=f"/listing/{listing.id}/"
                )

            # Delete old responses
            previous_responses.delete()

            return JsonResponse({
                'id': listing.id,
                'title': listing.title,
                'description': listing.description,
                'category': listing.category,
                'tags': [tag.name for tag in listing.tags.all()],
                'image_url': listing.image.url if listing.image else None,
                'listing_type': listing.listing_type,
                'status': listing.status,
                'duration': str(listing.duration),
                'edited_at': listing.edited_at.isoformat(),
            }, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'POST request required'}, status=405)

@login_required  # Make sure the user is logged in to access this page
def edit_listing_page(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    if listing.creator!=request.user:
        return JsonResponse({'error': 'You can only edit your own service/request.'}, status=403)
    
    return render(request, 'edit_listing.html', {
        'listing': listing,
        'duration': listing.duration.seconds // 60,
    })

"""@login_required
@csrf_exempt
def get_profile(request):
    try:
        data = json.loads(request.body)
        username = data.get('username')
        user = User.objects.get(username=username)

        profile = {
            'name': user.name,
            'picture': user.picture.url if user.picture else None,
            'title': user.title,
            'location': user.location,
            'bio': user.bio if user.bio else None,
            'link': user.link if user.link else None,
        }

        return JsonResponse({"status": "success", "data": profile}, status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)"""





"""@csrf_exempt
def create_profile(request):
    verified_user_data = request.session.get('verified_user_data')
    if not verified_user_data:
        return redirect('create_account')
    
    if request.method=='POST':
        form = ProfileCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = User.objects.create(
                username=verified_user_data['username'],
                email=verified_user_data['email'],
                password=verified_user_data['password'],
                is_active=True,
                is_verified=True
            )
            user.set_password(verified_user_data['password'])  # Set the password correctly
            
            user.name = form.cleaned_data['name']
            user.title = form.cleaned_data['title']
            user.location = form.cleaned_data['location']
            user.picture = form.cleaned_data['picture']
            user.bio = form.cleaned_data.get('bio', '')
            user.link = form.cleaned_data.get('link', '')

            user.save()
            del request.session['verified_user_data']

            return redirect('login')  # Redirect to login page
    else:
        form = ProfileCreationForm()
    
    return render(request, 'create_profile.html', {'form': form})"""

@login_required
@csrf_exempt
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            if form.cleaned_data.get('picture') is None:
                # set default user picture
                request.user.picture = 'static/images/default-avatar-profile-icon-social-600nw-1677509740.jpg.webp'
            form.save()
            return redirect('profile_info')  
    else:
        form = ProfileEditForm(instance=request.user)
    return render(request, 'edit_profile.html', {'form': form})


# @login_required
# def get_profile(request):
#     return render(request, 'profile_info.html', {'user': request.user})

# views.py

from django.db.models import Avg
from django.db.models import Sum

@login_required
def profile_info(request, user_id=None):
    user = get_object_or_404(User, id=user_id) if user_id else request.user

    reviews = Feedback.objects.filter(provider=user).exclude(
        details__isnull=True
    ).exclude(details__exact='').order_by('-created_at')

    # Calculate earned credits
    total_credits = ServiceTransaction.objects.filter(
        provider=user, status='Completed'
    ).aggregate(
        total_credits=Sum(models.F('duration') * models.F('multiplier') / 60)
    )['total_credits'] or 0

    # Fetch required data
    offered_services = Listing.objects.filter(creator=user, listing_type="Offer")
    requested_services = Listing.objects.filter(creator=user, listing_type="Request")
    
    if request.method == 'POST' and user == request.user:
        if 'add_skill' in request.POST:
            skill_names = request.POST.getlist('skills')
            for skill_name in skill_names:
                if skill_name.strip():
                    skill, _ = Skill.objects.get_or_create(name=skill_name.strip())
                    user.skills.add(skill)
        if 'remove_skill' in request.POST:
            to_remove = request.POST['remove_skill']
            skill = Skill.objects.get(id=to_remove)
            if skill:
                skill.delete()

    skills = user.skills.all()

    # Calculate multiplier if missing
    multiplier = user.multiplier

    # Update the context
    context = {
        'user': user,
        'offered_services': offered_services,
        'requested_services': requested_services,
        'skills': skills,
        'total_credits': total_credits,
        'multiplier': multiplier,
        'reviews': reviews
    }

    return render(request, 'profile_info.html', context)



@login_required
def delete_profile_picture(request):
    if request.method == "POST":
        user = request.user
        if user.picture:
            user.picture.delete()  # This deletes the file from storage
            user.picture = None    # Set the picture field to None
            user.save()
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"success": False, "error": "No profile picture to delete."})
    return JsonResponse({"success": False, "error": "Invalid request method."})

def add_service(request):
    # Logic for adding a service goes here
    return render(request, 'add_service.html')
def request_service(request):
    # Logic for adding a service goes here
    return render(request, 'request_service.html')

@login_required    
def my_service(request):
    listings = Listing.objects.filter(creator=request.user)
    
    return render(request, 'myservice.html', {'listings': listings})

@login_required   
@csrf_exempt 
def view_applicants(request, listing_id):
    responses = ListingResponse.objects.filter(listing_id=listing_id)
    # This service is dealt
    for response in responses:
        if response.status == 2:
            return render(request, 'view_applicants.html', {'response': response})

    if request.method == 'POST':
        response_id = request.POST.get('response_id')
        
        response = get_object_or_404(ListingResponse, id=response_id)
        response.message = 'Accepted'  
        response.status = 2
        response.save()
        Notification.objects.create(
            user=response.user,
            message="An update on your application.",
            url="/services"
        )
        listing = get_object_or_404(Listing, id=listing_id)
        listing.status = "In Progress"
        listing.save()
        for rresponse in responses:
            if rresponse != response:
                rresponse.message = 'Declined'  
                rresponse.status = 3
                rresponse.save()
                Notification.objects.create(
                    user=rresponse.user,
                    message="An update on your application.",
                    url="/services"
                )

        return redirect('view_applicants', listing_id=listing_id)

    return render(request, 'view_applicants.html', {'responses': responses})


@login_required   
def get_notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    data = [
        {"id": n.id, "message": n.message, "is_read": n.is_read, "created_at": n.created_at.strftime('%Y-%m-%d %H:%M:%S'), "url":n.url}
        for n in notifications
    ]
    return JsonResponse({"notifications": data})

@csrf_exempt 
def mark_as_read(request, notification_id):
    if request.method == "POST":
        notification = get_object_or_404(Notification, id=notification_id)
        notification.is_read = True
        notification.save()
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"}, status=400)

@login_required    
def applied_services(request):
    responses = ListingResponse.objects.filter(user=request.user)
    
    return render(request, 'applied_services.html', {'responses': responses})


@login_required
@csrf_exempt
def delete_listing(request, listing_id):
    if request.method == 'POST':
        try:
            listing = get_object_or_404(Listing, id=listing_id)
            for r in ListingResponse.objects.filter(listing=listing):
                r.delete()

            listing.delete()

            return redirect('my_service')

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return render(request, 'delete_listing.html')