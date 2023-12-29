from django.contrib import admin
from .models import Router, Peering


@admin.register(Router)
class RouterAdmin(admin.ModelAdmin):
	list_display = ['location', 'active', 'host_internal', 'host_external', 'wg_last_port']
	list_filter = ['active']


@admin.register(Peering)
class PeeringAdmin(admin.ModelAdmin):
	list_display = ['asn', 'router', 'active', 'mbgp_enabled', 'endpoint', 'last_up']
	list_filter = ['active', 'mbgp_enabled', 'router']
