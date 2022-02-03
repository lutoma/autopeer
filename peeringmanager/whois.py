from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import subprocess


def get_whois_field(obj, field):
	try:
		r = subprocess.run(['whois', '-h', 'whois.dn42', obj], stdout=subprocess.PIPE)
		r.check_returncode()
		whois_data = r.stdout.decode()
	except Exception:
		raise ValidationError(_('Could not connect to dn42 whois servers.'))

	if len(whois_data) < 1:
		return None

	whois_data = whois_data.splitlines()

	values = list()
	for line in whois_data:
		line = line.strip()

		if not line or line.startswith('%'):
			continue

		key, value = line.split(':', maxsplit=1)
		value = value.strip()

		if key == field:
			values.append(value)

	return values
