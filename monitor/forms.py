from django import forms

class DeviceFilterForm(forms.Form):
	name = forms.CharField(required=False, label="Name")
	device_type = forms.ChoiceField(
		required=False,
		choices=[('', 'All')] + [('router', 'Router'), ('server', 'Server'), ('client', 'Client')],
		label="Device Type"
	)
	status = forms.ChoiceField(
		required=False,
		choices=[('', 'All'), ('online', 'Online'), ('offline', 'Offline')],
	)
