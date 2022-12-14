from rest_framework import serializers

from djangoProject.common import ConfessionOrCommentInSerializerUnique, get_current_session
from member.models import User
from . import models


class ReportSerializer(ConfessionOrCommentInSerializerUnique):
    voters = serializers.SlugRelatedField(slug_field='handle', many=True, read_only=True)
    _duplicate_error = "You already reported the targeted confession/comment."

    class Meta:
        model = models.Report
        fields = '__all__'
        read_only_fields = ('session',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'request' in self.context and self.context['request'].user.role != 'admin':
            self.fields.pop('session')

    def create(self, validated_data):
        validated_data['session'] = get_current_session(self.context['request'])
        return super().create(validated_data)


class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.SlugRelatedField(queryset=User.objects.all(), slug_field='handle')
    receiver = serializers.SlugRelatedField(queryset=User.objects.all(), slug_field='handle', required=True)

    class Meta:
        model = models.Message
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'request' in self.context and (self.context['request'].method != 'GET' or
                                          self.context['request'].user.role != 'admin'):
            self.fields['sender'] = serializers.HiddenField(default=serializers.CurrentUserDefault())

    def validate_receiver(self, value):
        if self.context['request'].user == value:
            raise serializers.ValidationError("You can't send a message to yourself.")
        return value


class MessageListSerializer(serializers.Serializer):
    # id = serializers.IntegerField(source='target_id')
    handle = serializers.CharField(source='target_handle')
    count = serializers.IntegerField()

