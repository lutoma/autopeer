# coding: utf-8

from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.db import models

class Router(models.Model):
	location = models.CharField(max_length = 100, verbose_name = _('Location'))
	host_external = models.CharField(max_length = 100, verbose_name = _('External host'))
	host_internal = models.CharField(max_length = 100, verbose_name = _('Internal host'))
	ip_internal = models.CharField(max_length = 100, verbose_name = _('Internal IP'))
	wg_last_port = models.IntegerField(verbose_name = _('Last allocated wireguard port'), default = 42400)
	active = models.BooleanField(default = True, verbose_name = _('Active'), help_text = _('Users can only create peerings to active routers'))

	def __str__(self):
		return self.location

class Peering(models.Model):
	ROUTER_CHOICES = (
		('at-grz.gw.lutoma.dn42', 'Graz, Austria'),
		('de-scn.gw.lutoma.dn42', 'Saarbrücken, Germany'),
		('ca-mon.gw.lutoma.dn42', 'Montréal, Canada'),
		('us-lax.gw.lutoma.dn42', 'Los Angeles, USA'),
	)

	BANDWIDTH_CHOICES = (
		(21, '≥0.1mbit'),
		(22, '≥1mbit'),
		(23, '≥10mbit'),
		(24, '≥100mbit'),
		(25, '≥1gbit'),
	)

	VPN_CHOICES = (
		('wireguard', _('Wireguard')),
	)

	owner = models.ForeignKey(User, verbose_name = _('Owner'))
	asn = models.BigIntegerField(verbose_name = _('AS Number'), help_text = _('Your MNTNER object must be listed as mnt-by for the AS'))
	vpn_type = models.CharField(max_length = 50, choices = VPN_CHOICES, verbose_name = _('VPN type'), default = 'wireguard', help_text = _('Peering is also possible using OpenVPN/GRE/…, but only with manual setup for now.'))
	endpoint = models.CharField(max_length = 200, verbose_name = _('Wireguard endpoint'), help_text = _('Hostname/IP and port, e.g. example.org:1234, 127.0.0.1:1234, [::1]:1234'))
	endpoint_internal = models.GenericIPAddressField(protocol='IPv4', verbose_name = _('Internal router IP'), help_text = _('The routers IP within dn42. This will be used for the BGP session'))
	router = models.ForeignKey(Router, verbose_name = _('Router'))
	bandwidth_community = models.IntegerField(choices = BANDWIDTH_CHOICES, default = 24, verbose_name = _('Link bandwidth'), help_text = _('Used to set <a href=\'https://wiki.dn42/howto/Bird-communities\'>BGP communities</a>'))
	name = models.CharField(max_length = 25, verbose_name = _('Peering name'), help_text = _('Used for the interface name (wg.name) and bird peering name etc.'))

	wg_privkey = models.CharField(max_length = 150, verbose_name = _('Wireguard private key'))
	wg_pubkey = models.CharField(max_length = 150, verbose_name = _('Wireguard public key'))
	wg_peer_pubkey = models.CharField(max_length = 150, verbose_name = _('Wireguard public key'), help_text = _('See <a href=\'https://www.wireguard.com/quickstart/#key-generation\'>Wireguard manual</a> on how to generate the keys'))
	wg_port = models.IntegerField(verbose_name = _('Wireguard port'))

	def get_absolute_url(self):
		return '/peerings/{}/'.format(self.id)

	def __str__(self):
		return 'Peering with AS{} at {}'.format(self.asn, self.router)

	class Meta:
		unique_together = [('asn', 'router'), ('router', 'wg_port'), ('endpoint_internal', 'router')]
		verbose_name = _('Peering')
		verbose_name_plural = _('Peerings')
