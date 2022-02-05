from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import FormView, CreateView
from django.core.exceptions import ValidationError
from django.core.exceptions import PermissionDenied
from peeringmanager.whois import whois_query
from autopeer.email import send_email
from django.contrib.auth import login
from django.conf import settings
from dn42auth.models import DN42User
from autopeer.mixins import AuthenticatedRedirectMixin
from peeringmanager.models import Peering
from django import forms
import jwt
import re


class VerificationForm(forms.Form):
	name = forms.CharField(label='Maintainer',
		widget=forms.TextInput(attrs={'placeholder': 'FOOBAR-MNT'}),
		help_text=_('Please enter your mntner object as it exists in the DN42 registry, including the -MNT suffix.'))

	def clean(self):
		if 'name' not in self.cleaned_data:
			return super().clean()

		self.cleaned_data['name'] = self.cleaned_data['name'].upper()
		name = self.cleaned_data['name']

		if DN42User.objects.filter(dn42_mntner=name).exists():
			raise ValidationError({'name': 'This maintainer object is already registered with an account. Ping lutoma if you have forgotten your login details.'})

		mntner = whois_query(name)
		if not mntner:
			raise ValidationError({'name': 'Could not find an object by this name in the registry. If you only just registered it, try waiting a bit until caches have cleared.'})

		if 'mntner' not in mntner or mntner['mntner'][0] != name:
			raise ValidationError({'name': 'An object with this name exists in the registry, but it does not seem to be a mntner.'})

		if 'admin-c' not in mntner:
			raise ValidationError({'name': 'This mntner object does not seem to have an admin-c set.'})

		adminc_name = mntner['admin-c'][0]
		adminc = whois_query(adminc_name)
		if not adminc:
			raise ValidationError({'name': f'Could not find the admin-c object {adminc_name} listed in the mntner.'})

		if 'e-mail' in adminc:
			self.cleaned_data['email'] = adminc['e-mail'][0]
		else:
			# Try to find an email in the contact properties
			contact_methods = adminc['contact']

			for contact in contact_methods:
				# Look for something that could be an email - Does not match
				# all RFC compliant addresses but this is a fallback anyway
				sr = re.search(r'([^:@ \t]+@[-\.a-z0-9]+\.[-\.a-z0-9]+).*', contact, re.IGNORECASE)
				if sr:
					email = sr.group(1)

					# Some people have their irc nicks in a "nick@irc.hackint.org" format, filter those
					if 'irc' in email or 'hackint' in email:
						continue

					self.cleaned_data['email'] = email
					break

			if 'email' not in self.cleaned_data:
				raise ValidationError({'name': f'The admin-c object {adminc_name} does not seem to contain an email address.'})

		if 'nick' in adminc:
			self.cleaned_data['nick'] = adminc['nick'][0]
		elif 'person' in adminc:
			self.cleaned_data['nick'] = adminc['person'][0]
		else:
			self.cleaned_data['nick'] = name

		return super().clean()


class DN42VerificationView(AuthenticatedRedirectMixin, FormView):
	template_name = 'dn42auth/signup.html'
	form_class = VerificationForm
	success_url = '/signup/sent/'

	def form_valid(self, form):
		jwt_data = jwt.encode({
			'name': form.cleaned_data['name'],
			'nick': form.cleaned_data['nick'],
			'email': form.cleaned_data['email']
		}, settings.SECRET_KEY, algorithm='HS256')

		send_email(form.cleaned_data['email'], 'verification', {
			'name': form.cleaned_data['nick'],
			'signin_link': f'https://dn42.lutoma.org/signup/finish/{jwt_data}/'
		})

		return super().form_valid(form)


class SignupForm(forms.ModelForm):
	password = forms.CharField(widget=forms.PasswordInput())
	password_confirmation = forms.CharField(widget=forms.PasswordInput())

	def clean(self):
		if self.cleaned_data['password'] != self.cleaned_data['password_confirmation']:
			raise ValidationError({'password': '', 'password_confirmation': 'Passwords did not match.'})

	def save(self, commit=True):
		user = super().save(commit=False)
		user.set_password(self.cleaned_data['password'])
		if commit:
			user.save()
		return user

	class Meta:
		model = DN42User
		fields = ['email', 'password', 'password_confirmation']


class DN42SignupView(AuthenticatedRedirectMixin, CreateView):
	template_name = 'dn42auth/signup_auth.html'
	form_class = SignupForm
	success_url = '/peerings/'

	def dispatch(self, request, *args, **kwargs):
		try:
			self.jwt_data = jwt.decode(kwargs['jwt'], settings.SECRET_KEY, algorithms=['HS256'])
		except jwt.DecodeError:
			raise PermissionDenied()

		return super().dispatch(request, *args, **kwargs)

	def get_initial(self):
		initial = super().get_initial()
		initial['email'] = self.jwt_data['email']
		return initial

	def form_valid(self, form):
		form.instance.dn42_mntner = self.jwt_data['name']
		r = super().form_valid(form)

		# Assign any existing peerings with this mntner to the user
		Peering.objects.filter(mntner=self.jwt_data['name']).update(owner=form.instance)

		login(self.request, form.instance)
		return r
