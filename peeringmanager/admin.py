from django.contrib import admin
from .models import Router, Peering


@admin.register(Router)
class RouterAdmin(admin.ModelAdmin):
	list_display = ['location', 'active', 'host_internal', 'host_external', 'wg_last_port']
	list_filter = ['active']


@admin.register(Peering)
class PeeringAdmin(admin.ModelAdmin):
	list_display = ['asn', 'router', 'vpn_type', 'endpoint', 'endpoint_internal_v4',
		'endpoint_internal_v6', 'router_endpoint_internal_v6', 'mbgp_enabled']

	list_filter = ['router', 'vpn_type']
