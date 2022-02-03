import pystmark
from django.conf import settings


def send_email(to, template, data, attachments=[], tag=None):
	api_key = getattr(settings, 'POSTMARK_KEY', None)
	if not api_key:
		return

	email = pystmark.Message(sender='dn42-noreply@lutoma.org', to=to,
		template_alias=template, template_model=data, tag=(tag or template))

	for file in attachments:
		email.attach_binary(file[1], file[0])

	pystmark.send_with_template(email, api_key=api_key)
