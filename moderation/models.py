from django.core.validators import MinLengthValidator
from django.db import models


class Report(models.Model):
    session = models.ForeignKey('member.Session', on_delete=models.SET_NULL, null=True, blank=True)
    confession = models.ForeignKey('confession.Confession', on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey('confession.Comment', on_delete=models.CASCADE, null=True, blank=True)
    reason = models.CharField(max_length=1000, validators=[MinLengthValidator(15)])
    voters = models.ManyToManyField('member.User')
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('pk',)

    def __str__(self):
        return 'Report #%d: %s%s (%s)' % (self.pk, self.confession, self.comment, self.session)


class Message(models.Model):
    sender = models.ForeignKey('member.User', on_delete=models.CASCADE, related_name='sender')
    text = models.CharField(max_length=1000, validators=[MinLengthValidator(3)])
    receiver = models.ForeignKey('member.User', on_delete=models.CASCADE, related_name='receiver')
    sent = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-pk',)

    def __str__(self):
        return 'Message #%d, from %s to %s' % (self.pk, self.sender, self.receiver)

