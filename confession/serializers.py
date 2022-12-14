from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.permissions import SAFE_METHODS
from drf_recaptcha.fields import ReCaptchaV3Field

from djangoProject.common import ConfessionOrCommentInSerializerUnique
from djangoProject.taggit_serializer import TaggitSerializer, TagListSerializerField
from member.models import Session
from . import models


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Category
        fields = '__all__'

    def validate(self, attrs):
        attrs['name'] = attrs['name'].capitalize()
        return attrs


class RecaptchaSerializer(serializers.Serializer):
    recaptcha = ReCaptchaV3Field(action='submit')

    def validate(self, attrs):
        attrs.pop('recaptcha')
        return super().validate(attrs)


class ConfessionSerializer(TaggitSerializer, RecaptchaSerializer, serializers.ModelSerializer):
    categories = serializers.SerializerMethodField()
    comment_count = serializers.IntegerField(read_only=True)
    reaction_count = serializers.IntegerField(read_only=True)
    tags = TagListSerializerField()

    class Meta:
        model = models.Confession
        fields = '__all__'
        read_only_fields = ('created',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'request' in self.context:
            if self.context['request'].method not in SAFE_METHODS:
                self.fields['author'] = serializers.HiddenField(default=None)
            elif self.context['request'].user.is_anonymous or self.context['request'].user.role != 'admin':
                self.fields.pop('author')

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        validated_data.pop('is_approved', None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('author', None)
        if instance.author != self.context['request'].user and self.context['request'].user.role != 'admin':
            validated_data.pop('title', None)
            validated_data.pop('text', None)
        if instance.author == self.context['request'].user or self.context['request'].user.role not in ['admin', 'moderator']:
            validated_data.pop('is_approved', None)
        return super().update(instance, validated_data)

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_categories(self, obj):
        return obj.categories.values_list('name', flat=True)


class BaseCommentReactionSerializer(RecaptchaSerializer, serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'request' in self.context:
            if self.context['request'].method == 'POST':
                self.fields['sender'] = serializers.HiddenField(default=Session.objects.get(ip_address=self.context['request'].META['REMOTE_ADDR']))
            elif self.context['request'].user.is_anonymous or self.context['request'].user.role != 'admin':
                self.fields.pop('sender')


class CommentSerializer(BaseCommentReactionSerializer):
    class Meta:
        model = models.Comment
        fields = '__all__'
        read_only_fields = ('created', 'sender')


class ReactionSerializer(ConfessionOrCommentInSerializerUnique, BaseCommentReactionSerializer):
    _duplicate_error = "You already gave reaction to the targeted confession/comment."

    class Meta:
        model = models.Reaction
        fields = '__all__'
        read_only_fields = ('created', 'sender')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'request' in self.context and self.context['request'].method != 'POST':
            self.fields['confession'].read_only = True
            self.fields['comment'].read_only = True

