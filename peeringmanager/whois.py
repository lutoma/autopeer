from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import subprocess


def whois_query(obj):
	try:
		r = subprocess.run(['whois', '-h', 'whois.dn42', obj], stdout=subprocess.PIPE)
		r.check_returncode()
		whois_data = r.stdout.decode()
	except Exception:
		raise ValidationError(_('Could not connect to dn42 whois servers.'))

	if len(whois_data) < 1:
		return None

	whois_data = whois_data.splitlines()

	data = dict()
	for line in whois_data:
		line = line.strip()

		if not line or line.startswith('%'):
			continue

		try:
			key, value = line.split(':', maxsplit=1)
		except ValueError:
			continue

		key = key.strip()
		value = value.strip()

		if key not in data:
			data[key] = [value]
		else:
			data[key].append(value)

	return data


def get_whois_field(obj, field):
	data = whois_query(obj)
	if field not in data:
		return None

	return data[field]
