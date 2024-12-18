from django.contrib import admin
from .models import Listing, User, Tag, ListingResponse, Notification, ServiceTransaction

admin.site.register(Listing)
admin.site.register(User)
admin.site.register(Tag)
admin.site.register(ListingResponse)
admin.site.register(Notification)
admin.site.register(ServiceTransaction)