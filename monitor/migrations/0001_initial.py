# Generated by Django 5.1.4 on 2025-03-06 09:45

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='NetworkDevice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('device_type', models.CharField(choices=[('router', 'Router'), ('server', 'Server'), ('client', 'Client'), ('switch', 'Switch'), ('unknown', 'Unknown')], max_length=120)),
                ('name', models.CharField(default='no_value', max_length=100)),
                ('ssh_username', models.CharField(default='root', max_length=50)),
                ('status', models.CharField(default='unknown', max_length=20)),
                ('last_updated', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Connection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source', models.ForeignKey(db_column='source_id', on_delete=django.db.models.deletion.CASCADE, related_name='connections_out', to='monitor.networkdevice')),
                ('target', models.ForeignKey(db_column='target_id', on_delete=django.db.models.deletion.CASCADE, related_name='connections_in', to='monitor.networkdevice')),
            ],
        ),
        migrations.CreateModel(
            name='NetworkInterface',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('interface_name', models.CharField(max_length=50)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('mac_address', models.CharField(max_length=17)),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='monitor.networkdevice')),
            ],
        ),
    ]
