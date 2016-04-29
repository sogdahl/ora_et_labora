__author__ = 'Jurek'

from django.conf.urls import include, url
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'games', views.GameViewSet, base_name='game')
#router.register(r'choices/(?P<question>\d+)', views.ChoiceViewSet, base_name='choice')

app_name = 'game'

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^', include(router.urls)),
    url(r'^(?P<pk>\d+)/$', views.GameDetailView.as_view(), name='detail'),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]