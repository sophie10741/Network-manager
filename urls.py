from django.urls import include, path
from . import views

urlpatterns = [
	path('monitor/', include('monitor.urls')),
	path('devices/<int:pk>/ssh/', views.ssh_command_view, name='ssh_command'),
]
