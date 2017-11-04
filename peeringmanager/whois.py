# coding: utf-8
import pythonwhois

def get_whois_field(obj, field):
	try:
		whois_data = pythonwhois.net.get_whois_raw(obj, server='whois.dn42')
	except:
		raise ValidationError(_('Could not connect to dn42 whois servers.'))

	if len(whois_data) < 1:
		return None

	whois_data = whois_data[0].splitlines()

	values = list()
	for line in whois_data:
		line = line.strip()

		if not line or line.startswith('%'):
			continue

		key, value = line.split(':', maxsplit = 1)
		value = value.strip()

		if key == field:
			values.append(value)

	return values