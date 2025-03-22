import asyncio
from django.db import models
from .ping_check import check_ping
from .snmp_check import get_snmp_data
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

class NetworkDevice(models.Model):
    name = models.CharField(max_length=50)
    device_type = models.CharField(max_length=120, choices=[
        ('router', 'Router'),
        ('server', 'Server'),
        ('client', 'Client'),
        ('switch', 'Switch'),
        ('unknown', 'Unknown')
    ])

    def __str__(self):
        return f"{self.name}"

    name = models.CharField(max_length=100, default="no_value")
    ssh_username = models.CharField(max_length=50, default="root")
    status = models.CharField(max_length=20, default='unknown')
    last_updated = models.DateTimeField(auto_now=True)

    # def is_online(self):
    # return check_ping(self.ip_address)

    """	def get_snmp_info(self):
            oid = "1.3.6.1.2.1.1.1.0"
	    try:
		return asyncio.run(get_snmp_data(self.ip_address, oid))
		except Exception as e:
	           return f"Error: {str(e)}" """


class Connection(models.Model):
    source = models.ForeignKey('NetworkDevice', on_delete=models.CASCADE, related_name="connections_out",
                               db_column="source_id")
    target = models.ForeignKey('NetworkDevice', on_delete=models.CASCADE, related_name="connections_in",
                               db_column="target_id")

    def str(self):
        return f"{self.source.name} → {self.target.name}"


class NetworkInterface(models.Model):
    device = models.ForeignKey(NetworkDevice, on_delete=models.CASCADE)
    interface_name = models.CharField(max_length=50)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    mac_address = models.CharField(max_length=17)

    def is_online(self):
        interfaces = self.networkinterface_set.all()
        for interface in interfaces:
            if interface.ip_address:
                return check_ping(interface.ip_address)
        return False

    def get_snmp_info(self):
        oid = "1.3.6.1.2.1.1.1.0"
        try:
            return asyncio.run(get_snmp_data(self.ip_address, oid))
        except Exception as e:
            return f"Error: {str(e)}"

    def __str__(self):
        device_name = NetworkDevice.objects.get(id=f"{self.device.id}")
        return f"{device_name.name} - ({self.ip_address})"


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()

    def str(self):
        return self.name


class Utility(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    content = models.TextField()  # Содержимое команды или мануала
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='utilities')
    created_at = models.DateTimeField(auto_now_add=True)

    def str(self):
        return self.title


class Note(models.Model):
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    content = models.TextField(verbose_name="Текст")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    def __str__(self):
        return self.title


class Comment(models.Model):
    note = models.ForeignKey(Note, related_name='comments', on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(verbose_name="Комментарий")
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Комментарий от {self.author} к '{self.note}'"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20, blank=True, null=True)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()