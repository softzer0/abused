from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.db import models
from taggit.managers import TaggableManager

from djangoProject.common import EMOJI_PATTERN


class Category(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return 'Category: %s' % self.name


class Confession(models.Model):
    title = models.CharField(max_length=255, validators=[MinLengthValidator(3)])
    text = models.TextField(max_length=5000, validators=[MinLengthValidator(200)])
    author = models.ForeignKey('member.User', on_delete=models.SET_NULL, null=True)
    is_approved = models.BooleanField(default=False)
    categories = models.ManyToManyField(Category)
    tags = TaggableManager()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-pk',)

    def __str__(self):
        return 'Confession %s: %s' % (self.author, self.title)


class Comment(models.Model):
    sender = models.ForeignKey('member.Session', on_delete=models.SET_NULL, null=True)
    confession = models.ForeignKey(Confession, on_delete=models.CASCADE)
    text = models.CharField(max_length=255, validators=[MinLengthValidator(3)])
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return 'Comment %s: #%d' % (self.sender, self.pk)


def check_if_emoji(value):
    if not EMOJI_PATTERN.fullmatch(value):
        raise ValidationError("%(value)s is not an Emoji" % {'value': value})


class Reaction(models.Model):
    sender = models.ForeignKey('member.Session', on_delete=models.SET_NULL, null=True)
    confession = models.ForeignKey(Confession, on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    emoji = models.CharField(max_length=1, validators=[check_if_emoji])
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return 'Reaction %s: %s%s' % (self.sender, self.confession, self.comment)

