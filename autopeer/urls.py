from django.urls import path, include
from django.contrib import admin

from peeringmanager.views import (
	PeeringView, PeeringDetailView, UpdatePeeringView, CreatePeeringView
)

urlpatterns = [
	path('', PeeringView.as_view(), name='index'),
	path('peerings/<int:pk>/', PeeringDetailView.as_view(), name='peerings-detail'),
	path('peerings/<int:pk>/edit/', UpdatePeeringView.as_view(), name='peerings-edit'),
	path('peerings/new/', CreatePeeringView.as_view(), name='peerings-new'),
	#path('accounts/login/', login, name='login'),
	path('accounts/', include('django.contrib.auth.urls')),
	path('admin/', admin.site.urls),
]
