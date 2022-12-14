from rest_framework import serializers
from django.utils import timezone
from . import models
from .models import Session


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        exclude = ('is_password_custom',)
        read_only_fields = ('last_login', 'role')

    def __init__(self, *args, **kwargs):
        is_auth = kwargs.pop('is_auth', None)
        super().__init__(*args, **kwargs)

        if is_auth:
            self.fields.pop('id')
            self.fields['handle'].validators.pop(0)
            self.fields['handle'].required = True
            self.fields['password'].required = True
        elif 'request' in self.context and self.context['request'].user.is_authenticated:
            if self.context['request'].user.role != 'admin':
                self.fields.pop('id')
                self.fields.pop('role')
            if self.context['request'].user.is_password_custom:
                self.fields.pop('password')

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            instance.set_password(validated_data.pop('password'))
            instance.is_password_custom = True
        return super().update(instance, validated_data)


class BlocklistSerializer(serializers.ModelSerializer):
    session = serializers.SlugRelatedField(slug_field='ip_address', queryset=Session.objects.all())

    class Meta:
        model = models.Blocklist
        fields = '__all__'

    def validate_user(self, value):
        if self.context['request'].user == value:
            raise serializers.ValidationError("You can't block yourself.")
        return value

    def validate_expires(self, value):
        if value and timezone.now() > value:
            raise serializers.ValidationError("You can't set a point in the past.")
        return value

