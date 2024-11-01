from django.contrib import admin
from .models import Listing, User, Tag

admin.site.register(Listing)
admin.site.register(User)
admin.site.register(Tag)
