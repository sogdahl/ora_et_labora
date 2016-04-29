from django.views import generic
from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response

from .models import Game
from .serializers import GameSerializer


class IndexView(generic.ListView):
    context_object_name = 'active_games_list'

    def get_queryset(self):
        """Return the last five games."""
        return Game.objects.filter(
        ).order_by('-id')[:5]


class GameDetailView(generic.DetailView):
    model = Game

    def get_queryset(self):
        return Game.objects.filter()


class GameViewSet(viewsets.ModelViewSet):
    serializer_class = GameSerializer
    queryset = Game.objects.all()

    @list_route()
    def latest(self, request):
        """Return the last five published questions."""
        questions = Game.objects.filter(
        ).order_by('-id')[:5]

        page = self.paginate_queryset(questions)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(questions, many=True)
        return Response(serializer.data)