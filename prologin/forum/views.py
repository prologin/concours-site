from django.shortcuts import render
from django.views import generic
from forum.models import Category, Post

class CategoryView(generic.ListView):
    model = Category
    template_name = 'forum/home.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.all().order_by('display')
