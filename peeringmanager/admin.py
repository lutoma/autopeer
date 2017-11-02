from django.contrib import admin
from .models import *

@admin.register(Router)
class RouterAdmin(admin.ModelAdmin):
	pass

@admin.register(Peering)
class PeeringAdmin(admin.ModelAdmin):
	pass