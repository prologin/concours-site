from django.http import HttpResponse
from django.views import generic
from django.utils import timezone
from django.utils.html import escape
from news.models import News
import json

class IndexView(generic.ListView):
    template_name = 'news/index.html'
    context_object_name = 'latest_news_list'

    def get_queryset(self):
        return News.objects.order_by('-pub_date')[:1]

class RSSView(generic.ListView):
    template_name = 'news/rss.html'
    context_object_name = 'latest_news_list'
    content_type = 'application/xml'

    def get_queryset(self):
        return News.objects.order_by('-pub_date')

class DetailView(generic.DetailView):
    model = News
    template_name = 'news/detail.html'

def latest(request, offset, nb):
    offset = int(offset)
    nb = int(nb) + offset
    lst = News.objects.order_by('-pub_date')[offset:nb]
    data = []
    for el in lst:
        data.append({
            'id': el.id,
            'title': escape(el.title),
        })
    return HttpResponse(json.dumps(data))
