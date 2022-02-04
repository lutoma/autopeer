from django.urls import path
from django.contrib import admin
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views

from dn42auth.views import DN42VerificationView, DN42SignupView
from peeringmanager.views import (
	PeeringView, PeeringDetailView, UpdatePeeringView, CreatePeeringView
)

urlpatterns = [
	path('', TemplateView.as_view(template_name='index.html'), name='index'),
	path('peerings/', PeeringView.as_view(), name='peering'),
	path('peerings/<int:pk>/', PeeringDetailView.as_view(), name='peerings-detail'),
	path('peerings/<int:pk>/edit/', UpdatePeeringView.as_view(), name='peerings-edit'),
	path('peerings/new/', CreatePeeringView.as_view(), name='peerings-new'),

	path('change-password/', auth_views.PasswordChangeView.as_view()),
	path('login/', auth_views.LoginView.as_view()),
	path('logout/', auth_views.LogoutView.as_view()),
	path('signup/sent/', TemplateView.as_view(template_name='dn42auth/signup_sent.html'), name='signup-sent'),

	path('signup/', DN42VerificationView.as_view(), name='signup-verification'),
	path('signup/finish/<str:jwt>/', DN42SignupView.as_view(), name='signup-auth'),
	path('admin/', admin.site.urls),
]
