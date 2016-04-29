from __future__ import unicode_literals

import datetime
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import F
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')

    def was_published_recently(self):
        now = timezone.now()
        return now >= self.pub_date >= now - datetime.timedelta(days=1)
    was_published_recently.admin_order_field = 'pub_date'
    was_published_recently.boolean = True
    was_published_recently.short_description = 'Published recently?'

    def __str__(self):
        return self.question_text


@python_2_unicode_compatible
class Choice(models.Model):
    question = models.ForeignKey(Question)
    choice_text = models.CharField(max_length=200)
    votes = models.PositiveIntegerField(default=0)

    def vote(self):
        # This is written this way so that the DB is the one incrementing the value & not the model/Django/Python.
        # That way, if there are multiple threads running and 2 Choice methods both increment the .value field,
        # they don't overwrite each other.
        if not self.pk:
            raise ObjectDoesNotExist
        Choice.objects.filter(pk=self.pk).update(votes=F('votes') + 1)
        self.refresh_from_db()

    def __str__(self):
        return self.choice_text