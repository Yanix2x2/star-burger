from django.contrib import admin

from .models import AddressPoint


@admin.register(AddressPoint)
class AddressPointAdmin(admin.ModelAdmin):
    pass
