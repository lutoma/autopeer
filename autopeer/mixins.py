from django.http import HttpResponseRedirect


class AuthenticatedRedirectMixin:
	def dispatch(self, request, *args, **kwargs):
		if self.request.user.is_authenticated:
			return HttpResponseRedirect('/peerings/')
		return super().dispatch(request, *args, **kwargs)
