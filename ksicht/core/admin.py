from django.contrib import admin

from cuser.admin import UserAdmin

from .models import User


admin.site.register(User, UserAdmin)
