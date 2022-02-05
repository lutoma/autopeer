from django.utils.translation import gettext_lazy as _
from dn42auth.models import DN42User
from hurry.filesize import size
from django.db import models
import rrdtool
import requests
import re


class Router(models.Model):
	location = models.CharField(max_length=100, verbose_name=_('Location'))
	host_external = models.CharField(max_length=100, verbose_name=_('External host'))
	host_internal = models.CharField(max_length=100, verbose_name=_('Internal host'))
	ip_internal = models.CharField(max_length=100, verbose_name=_('Internal IP'))
	flag_emoji = models.CharField(max_length=10, verbose_name=_('Location flag emoji'), default='🇪🇺')
	wg_last_port = models.IntegerField(verbose_name=_('Last allocated wireguard port'), default=42400)
	active = models.BooleanField(default=True, verbose_name=_('Active'),
		help_text=_('Users can only create peerings to active routers'))

	lg_id = models.CharField(verbose_name=_('Looking Glass ID'), max_length=150)

	def __str__(self):
		return f'{self.location} ({self.host_external})'

	class Meta:
		ordering = ['location']


class Peering(models.Model):
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

	owner = models.ForeignKey(DN42User, verbose_name=_('Owner'),
		on_delete=models.SET_NULL, null=True, blank=True)

	mntner = models.CharField(_('Maintainer object'), max_length=200)

	asn = models.BigIntegerField(verbose_name=_('AS Number'),
		help_text=_('Your maintainer object must be listed as mnt-by for the AS'))

	vpn_type = models.CharField(max_length=50, choices=VPN_CHOICES,
		verbose_name=_('VPN type'), default='wireguard',
		help_text=_('Peering is also possible using OpenVPN/GRE/…, but only with manual setup for now.'))

	endpoint = models.CharField(max_length=200, verbose_name=_('Wireguard endpoint'),
		help_text=_('Hostname/IP and port, e.g. example.org:1234, 127.0.0.1:1234, [::1]:1234'))

	endpoint_internal_v4 = models.GenericIPAddressField(protocol='IPv4',
		verbose_name=_('Internal IPv4 address'),
		help_text=_('Internal DN42 address of your router'))

	endpoint_internal_v6 = models.GenericIPAddressField(protocol='IPv6',
		verbose_name=_('Link-local IPv6 address'),
		help_text=_('Link-local IPv6 address of your router'))

	mbgp_enabled = models.BooleanField(default=True, verbose_name=_('Multi-protocol BGP over IPv6'),
		help_text=_('If set, the router will establish a Multi-protocol session for both IPv4 and IPv6 over the IPv6 link-local address (RFC 4760)'))

	router = models.ForeignKey(Router, verbose_name=_('Router'), on_delete=models.CASCADE)
	bandwidth_community = models.IntegerField(choices=BANDWIDTH_CHOICES, default=24,
		verbose_name=_('Link bandwidth'),
		help_text=_('Used to set <a href="https://dn42.eu/howto/Bird-communities">BGP communities</a>'))

	name = models.CharField(max_length=25, verbose_name=_('Peering name'),
		help_text=_('A human-readable name for this peering. Usually your nickname or a network name. Used for the Wireguard interface name, in the looking glass, and similar places. Lowercase ASCII only, max. 25 chars.'))

	wg_privkey = models.CharField(max_length=150, verbose_name=_('Wireguard private key'))
	wg_pubkey = models.CharField(max_length=150, verbose_name=_('Wireguard public key'))
	wg_peer_pubkey = models.CharField(max_length=150, verbose_name=_('Wireguard public key'),
		help_text=_('See <a href=\'https://www.wireguard.com/quickstart/#key-generation\'>Wireguard manual</a> on how to generate the keys'))

	wg_port = models.IntegerField(verbose_name=_('Wireguard port'))

	@property
	def endpoint_port(self):
		return self.endpoint.rsplit(':', maxsplit=1)[-1]

	def lg_request(self, req):
		req_data = {'servers': [self.router.lg_id], 'type': 'bird', 'args': req}
		res = requests.post('https://lg.dn42.lutoma.org/api/', json=req_data)
		return res.json()['result'][0]['data']

	def lg_route_count(self, table, constraint=''):
		data = self.lg_request(f'show route protocol {self.name} table {table} count {constraint}')
		regex_res = re.match(r'^([0-9]+) of.*$', data)
		return regex_res.group(1)

	def get_status(self):
		try:
			details = self.lg_request(f'show protocols all {self.name}')
			state_array = details.splitlines()[1].split()

			return {
				'state': state_array[5],
				'state_since': state_array[4],
				'routes_v4': self.lg_route_count('peers4'),
				'routes_v4_primary': self.lg_route_count('peers4', 'primary'),
				'routes_v4_filtered': self.lg_route_count('peers4', 'filtered'),
				'routes_v6': self.lg_route_count('peers6'),
				'routes_v6_primary': self.lg_route_count('peers6', 'primary'),
				'routes_v6_filtered': self.lg_route_count('peers6', 'filtered')
			}
		except Exception:
			return None

	def get_traffic(self):
		rrd = f'/var/lib/collectd/rrd/{self.router.host_external}/interface-wg.{self.name}/if_octets.rrd'
		try:
			data = rrdtool.graphv('-',
				f'DEF:tx={rrd}:tx:AVERAGE',
				f'DEF:rx={rrd}:rx:AVERAGE',
				'VDEF:txa=tx,AVERAGE',
				'VDEF:rxa=rx,AVERAGE',
				'PRINT:txa:%lf',
				'PRINT:rxa:%lf')

			return {
				'tx': size(float(data['print[0]'])),
				'rx': size(float(data['print[1]'])),
			}
			return data
		except Exception:
			return None

	def get_absolute_url(self):
		return f'/peerings/{self.id}/'

	def __str__(self):
		return f'Peering with AS{self.asn} at {self.router}'

	class Meta:
		unique_together = [
			('router', 'asn'),
			('router', 'wg_port'),
			('router', 'endpoint_internal_v4'),
			('router', 'name'),
		]

		verbose_name = _('Peering')
		verbose_name_plural = _('Peerings')
