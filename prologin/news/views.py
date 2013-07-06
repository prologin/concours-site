from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.template import RequestContext, loader
from django.shortcuts import render, get_list_or_404
from django.utils import timezone

def index(request):
    return render(request, 'news/index.html')
