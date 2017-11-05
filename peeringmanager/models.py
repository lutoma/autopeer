# coding: utf-8

from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from hurry.filesize import size
from django.db import models
import dateutil.parser
import rrdtool
import requests

class Router(models.Model):
	location = models.CharField(max_length = 100, verbose_name = _('Location'))
	host_external = models.CharField(max_length = 100, verbose_name = _('External host'))
	host_internal = models.CharField(max_length = 100, verbose_name = _('Internal host'))
	ip_internal = models.CharField(max_length = 100, verbose_name = _('Internal IP'))
	wg_last_port = models.IntegerField(verbose_name = _('Last allocated wireguard port'), default = 42400)
	active = models.BooleanField(default = True, verbose_name = _('Active'), help_text = _('Users can only create peerings to active routers'))
	lg_id = models.IntegerField(verbose_name = _('Looking Glass ID'), default = 0)

	def __str__(self):
		return self.location

	class Meta:
		ordering = ['location']

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

	def get_status(self):
		r = requests.get('https://lg.dn42.lutoma.org/api/routeservers/{}/neighbours'.format(self.router.lg_id))
		if r.status_code != requests.codes.ok:
			return None

		lg_data = r.json()
		status = list(filter(lambda x: x['id'] == self.name, lg_data['neighbours']))
		if not status:
			return

		status[0]['details']['state_changed'] = dateutil.parser.parse(status[0]['details']['state_changed'])
		return status[0]


	def get_traffic(self):
		rrd = '/var/lib/collectd/rrd/{}/interface-wg.{}/if_octets.rrd'.format(self.router.host_internal, self.name)
		try:
			data = rrdtool.graphv('-',
				'DEF:tx={}:tx:AVERAGE'.format(rrd),
				'DEF:rx={}:rx:AVERAGE'.format(rrd),
				'VDEF:txa=tx,AVERAGE',
				'VDEF:rxa=rx,AVERAGE',
				'PRINT:txa:%lf',
				'PRINT:rxa:%lf')

			return {
				'tx': size(float(data['print[0]'])),
				'rx': size(float(data['print[1]'])),
			}
			return data
		except:
			return None

	def get_absolute_url(self):
		return '/peerings/{}/'.format(self.id)

	def __str__(self):
		return 'Peering with AS{} at {}'.format(self.asn, self.router)

	class Meta:
		unique_together = [
			('router', 'asn'),
			('router', 'wg_port'),
			('router', 'endpoint_internal'),
			('router', 'name'),
		]

		verbose_name = _('Peering')
		verbose_name_plural = _('Peerings')
