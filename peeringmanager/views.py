from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django import forms
from subprocess import Popen, PIPE
from .models import Peering, Router
from .whois import get_whois_field
from io import StringIO
import fabric
import json
import re


@method_decorator(login_required, name='dispatch')
class PeeringView(ListView):
	model = Peering

	def get_queryset(self):
		return Peering.objects.filter(owner=self.request.user)


@method_decorator(login_required, name='dispatch')
class PeeringDetailView(DetailView):
	model = Peering

	def get_queryset(self):
		return Peering.objects.filter(owner=self.request.user)


class PeeringForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		self.user = kwargs.pop('user')
		super().__init__(*args, **kwargs)
		self.fields['router'].queryset = Router.objects.filter(active=True)

	def clean_asn(self):
		mntby = get_whois_field('AS{}'.format(self.cleaned_data['asn']), 'mnt-by')
		if not mntby or self.user.dn42_mntner not in mntby:
			raise ValidationError(_('AS does not exist or user is not listed as mnt-by for this AS'))

		return self.cleaned_data['asn']

	def clean_endpoint_internal_v4(self):
		mntby = get_whois_field('{}'.format(self.cleaned_data['endpoint_internal_v4']), 'mnt-by')
		if self.user.dn42_mntner not in mntby:
			raise ValidationError(_('User is not listed as mnt-by for the internal router IP'))

		return self.cleaned_data['endpoint_internal_v4']

	def clean_endpoint(self):
		if not re.match(r'^(\[[0-9a-f\:]+\]|([0-9]{1,3}\.){3}[0-9]{1,3}|[-.a-zA-Z0-9]+\.[a-zA-Z]+)\:[0-9]{1,5}$', self.cleaned_data['endpoint']):
			raise ValidationError(_('Endpoint doesn\'t seem to be valid IP/hostname:port combo'))

		return self.cleaned_data['endpoint']

	def clean_wg_peer_pubkey(self):
		if len(self.cleaned_data['wg_peer_pubkey']) != 44:
			raise ValidationError(_('Wireguard public key has invalid length'))
		return self.cleaned_data['wg_peer_pubkey']

	class Meta:
		model = Peering
		fields = ['router', 'name', 'asn', 'vpn_type', 'endpoint', 'endpoint_internal_v4',
			'endpoint_internal_v6', 'mbgp_enabled', 'bandwidth_community', 'wg_peer_pubkey']


class PeeringMixin:
	form_class = PeeringForm
	template_name = 'peeringmanager/peering_form.html'

	def get_queryset(self):
		return Peering.objects.filter(owner=self.request.user)

	def get_form_kwargs(self):
		kwargs = super().get_form_kwargs()
		kwargs.update({'user': self.request.user})
		return kwargs

	def form_valid(self, form):
		form.instance.owner = self.request.user

		if not form.instance.wg_privkey or not form.instance.wg_pubkey:
			with Popen(["wg", "genkey"], stdout=PIPE) as proc:
				privkey = proc.stdout.read()
				form.instance.wg_privkey = privkey.decode('utf-8').strip()

			with Popen(["wg", "pubkey"], stdout=PIPE, stdin=PIPE) as proc:
				pubkey = proc.communicate(input=privkey)[0]
				form.instance.wg_pubkey = pubkey.decode('utf-8').strip()

		form.instance.router.wg_last_port += 1
		form.instance.wg_port = form.instance.router.wg_last_port
		form.instance.router.save()

		fields = ['id', 'asn', 'endpoint', 'endpoint_internal_v4', 'endpoint_internal_v6', 'mbgp_enabled',
			'bandwidth_community', 'wg_privkey', 'wg_peer_pubkey', 'wg_port', 'name']

		data = map(lambda c: (c, getattr(form.instance, c)), fields)
		data = json.dumps(dict(data))
		data_stream = StringIO(data)

		ssh_host = form.instance.router.host_external
		print(f'Connecting to {ssh_host} to update peering #{form.instance.id}')

		with fabric.Connection(ssh_host, user='autopeer', connect_timeout=5) as conn:
			conn.run('/usr/bin/sudo /usr/local/bin/autopeer-update', in_stream=data_stream)

		return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class CreatePeeringView(PeeringMixin, CreateView):
	pass


@method_decorator(login_required, name='dispatch')
class UpdatePeeringView(PeeringMixin, UpdateView):
	pass
