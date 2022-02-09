from django.http import HttpResponseRedirect
from django.utils import translation
from django.conf import settings


def switch_language(request, language):
	response = HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
	translation.activate(language)

	response.set_cookie(
		settings.LANGUAGE_COOKIE_NAME, language,
		max_age=settings.LANGUAGE_COOKIE_AGE,
		path=settings.LANGUAGE_COOKIE_PATH,
		domain=settings.LANGUAGE_COOKIE_DOMAIN)

	return response
