__author__ = 'Jurek'

from django.conf.urls import include, url
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'questions', views.QuestionViewSet, base_name='question')
router.register(r'choices/(?P<question>\d+)', views.ChoiceViewSet, base_name='choice')

app_name = 'polls'

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^', include(router.urls)),
    url(r'^(?P<pk>\d+)/$', views.DetailView.as_view(), name='detail'),
    url(r'^(?P<pk>\d+)/results/$', views.ResultsView.as_view(), name='results'),
    url(r'^(?P<question_id>\d+)/vote/$', views.vote, name='vote'),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]