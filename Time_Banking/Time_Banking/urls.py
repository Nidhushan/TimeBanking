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
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path('create-account/', views.create_account, name='create_account'),
    path("user/<int:id>/", views.user_detail, name="user_detail"),
    path("api/create-user/", views.create_user, name="create_user"),
    path("api/listings/", views.get_all_listings, name="get_all_listings"),
    path(
        "api/listings/<int:listing_id>/responses/",
        views.get_responses_for_listing,
        name="get_responses_for_listing",
    ),
    path(
        "api/listings/<int:listing_id>/availability/",
        views.get_availability_for_listing,
        name="get_availability_for_listing",
    ),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
