from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import requests
import json

class DN42Backend:
	def authenticate(self, username=None, password=None):
		username = username.upper()
		if not username.endswith('-MNT'):
			return None

		req = requests.post('https://util.sour.is/v1/reg/reg.auth',
			data=json.dumps({'username': username, 'password': password}),
			headers={'user-agent': 'lutoma-autopeer'})

		# API returns 403 for invalid usernames/passwords
		if req.status_code not in (200, 403):
			raise ValidationError(_('Error while querying the dn42 registry API'))

		if req.status_code == 200 and req.text == 'OK':
			return User.objects.get_or_create(username=username)[0]

		return None

	def get_user(self, user_id):
		try:
			return User.objects.get(pk=user_id)
		except User.DoesNotExist:
			return None
