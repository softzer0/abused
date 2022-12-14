import string
import random

from django.core.validators import MinLengthValidator
from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models


def generate_random_password():
    rnd_alphanum = random.choices(string.ascii_uppercase, k=4) + random.choices(string.digits, k=4)
    random.shuffle(rnd_alphanum)
    return ''.join(rnd_alphanum)


def generate_random_handle():
    return ''.join(random.choices(string.ascii_uppercase, k=8))


class User(AbstractBaseUser):
    password = models.CharField(default=generate_random_password, max_length=128, validators=[MinLengthValidator(8)])
    role = models.CharField(choices=(('admin', "Administrator"), ('moderator', "Moderator")), max_length=9, null=True, blank=True)
    handle = models.CharField(default=generate_random_handle, max_length=20, unique=True)
    is_password_custom = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'handle'
    REQUIRED_FIELDS = []


class Session(models.Model):
    ip_address = models.GenericIPAddressField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return 'Session %s (%s)' % (self.ip_address, self.user)


class Blocklist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, null=True, blank=True)
    expires = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('-pk',)
        constraints = (models.UniqueConstraint(fields=('user', 'session', 'expires'), name='blocklist_unique'),)

    def __str__(self):
        return 'Blocked %s%s, expires %s' % (self.session, self.user, self.expires)

