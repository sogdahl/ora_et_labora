__author__ = 'Jurek'
from django.db.models import Sum
from rest_framework import serializers

from .models import Question, Choice


class QuestionSerializer(serializers.ModelSerializer):
    total_votes = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ('id', 'question_text', 'pub_date', 'total_votes')

    def get_total_votes(self, obj):
        return Choice.objects.filter(question=obj).aggregate(Sum('votes'))['votes__sum']


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ('id', 'question', 'choice_text', 'votes')
        read_only_fields = ('id', 'votes')