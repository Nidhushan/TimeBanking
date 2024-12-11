"""
URL configuration for Time_Banking project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views
from . import views


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name='logout'),
    path('create-account/', views.create_account, name='create_account'),
    # path('verify/<str:code>/', views.verify_account, name='verify_account'),
    path('verification-sent/', TemplateView.as_view(template_name='verification_sent.html'), name='verification_sent'),  # Verification URL
    path('verification-success/', TemplateView.as_view(template_name='verification_successful.html'), name='verification_successful'),
    path('verification-failed/', TemplateView.as_view(template_name='verification_failed.html'), name='verification_failed'),
    path('resend-verification/', views.resend_verification_email, name='resend_verification_email'),
    path('verify/', views.verify_account_code, name='verify_account_code'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-reset-code/', views.verify_reset_code, name='verify_reset_code'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('create-listing/', views.create_listing_page, name='create_listing_page'),
    path('accepted-services/', views.accepted_services, name='accepted_services'),
    # path('submit-feedback/<int:transaction_id>/', views.submit_feedback, name='submit_feedback'),
    path('listing/<int:listing_id>/mark_completed/', views.mark_listing_completed, name='mark_listing_completed'),
    path('submit-feedback/<int:listing_id>/', views.submit_feedback, name='submit_feedback'),


    # path('add-service/', views.add_service, name='add_service'),
    # path('request-service/', views.request_service, name='request_service'),
    
    # path('login/', views.login, name='login'),

    path('accounts/login/', views.custom_login, name='login'),
    path("api/user/<int:id>/", views.user_detail, name="user_detail"),


    path("api/listings/", views.get_all_listings, name="get_all_listings"),
    # path('listing/<int:listing_id>/', views.get_listing_by_id, name='get_listing'),
    path('listing/<int:listing_id>/', views.view_listing, name='view_listing'),
    path('listing/<int:listing_id>/apply/', views.apply_service, name='apply_service'),
    path('listing/<int:listing_id>/edit/', views.edit_listing, name='edit_listing'),
    path('listing/<int:listing_id>/edit/page/', views.edit_listing_page, name='edit_listing_page'),
    # path(
    #     "api/listings/<int:listing_id>/responses/",
    #     views.get_responses_for_listing,
    #     name="get_responses_for_listing",
    # ),
    # path(
    #     "api/listings/<int:listing_id>/availability/",
    #     views.get_availability_for_listing,
    #     name="get_availability_for_listing",
    # ),
    path('api/change-password/', views.change_password, name='change_password'),
    path('api/delete-account/', views.delete_account, name='delete_account'),
    # path('api/update-user-settings/', views.update_user_settings, name='update_user_settings'),
    path('profile/', views.profile_info, name='profile_info'),
    #path('profile/create/', views.create_profile, name='create_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('delete-profile-picture/', views.delete_profile_picture, name='delete_profile_picture'),
    path('api/create-listing/', views.create_listing, name='create_listing'),
    # path('api/edit-listing/<int:listing_id>/', views.edit_listing, name='edit_listing'),
    path('api/categories/', views.get_categories, name='get_categories'),
    path('api/tags/', views.get_tags, name='get_tags'),
    #path('create-profile/', views.create_profile, name='create_profile'),
    # path('change-password/', views.change_password_page, name='change_password_page'),
    # path('delete-account/', views.delete_account_page, name='delete_account_page'),
    path('settings/', views.user_settings_page, name='user_settings_page'),
    
    path('create-listing/', views.create_listing_page, name='create_listing_page'),
    path('myservices/', views.my_service, name='my_service'),
    path('applicants/<int:listing_id>/', views.view_applicants, name='view_applicants'),
    path('get-notifications/', views.get_notifications, name='get_otifications'),
    path('appliedservices/', views.applied_services, name='applied_services'),
    path('notifications/mark-as-read/<int:notification_id>/', views.mark_as_read, name='mark_as_read'),
    path('user/<int:user_id>/', views.profile_info, name='user_profile'),
    path('listing/<int:id>/', views.view_listing, name='view_listing'),
    path('profile/<int:user_id>/', views.profile_info, name='profile_info'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
