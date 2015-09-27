import datetime

from django.views import generic
from django.shortcuts import render
from django.utils.text import slugify
from django.http import Http404 
from forum.models import Category, Post, Thread


from forum.forms import PostForm, ThreadFrom

class CategoryView(generic.ListView):
    model = Category
    template_name = 'forum/home.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.all().order_by('display')
        
        


def HomeTest(request):
    cats = Category.objects.all()
    current_url = request.get_full_path()
    if current_url == "/forum/": # home page for the forum
        return render(request, 'forum/home.html', {'cats':cats})
    else: # display the rest
        cat = current_url[7:]
        for CAT in cats:
            if cat.startswith(CAT.slug):
                urlLen = len(cat.split('/'))
                if urlLen == 1: #thread list
                    threads = Thread.objects.all().filter(category=CAT)
                    formThread = ThreadFrom(request.POST or None)
                    formPost = PostForm(request.POST or None)
                    if formThread.is_valid() & formPost.is_valid():
                        new_thread = formThread.save(commit=False)
                        new_post = formPost.save(commit=False)
                        new_thread.slug = slugify(new_thread.name)
                        new_thread.category = CAT
                        new_thread.created_by = request.user
                        new_thread.last_edited_by = request.user
                        new_thread.created_on = datetime.datetime.now()
                        new_thread.last_edited_on = datetime.datetime.now()
                        new_post.title = "noTitle"
                        new_post.slug = slugify(new_post.title)
                        new_post.category = CAT
                        new_post.created_by = request.user
                        new_post.created_on = datetime.datetime.now()
                        new_thread.save()
                        new_post.thread = new_thread
                        new_post.save()
                        formPost = PostForm()
                        formThread = ThreadFrom()
                    return render(request, 'forum/threadList.html', {'catName':CAT.name, 'description':CAT.description, 'threads':threads, 'slug':CAT.slug, 'formThread':formThread, 'formPost':formPost})
                else: # post
                    threads = Thread.objects.all().filter(category=CAT)
                    thread = None
                    slug = cat.split('/')[1]
                    for t in threads:
                        if slug == t.slug:
                            thread = t
                            break
                    if thread is None:
                        raise Http404 
                    posts = Post.objects.all().filter(category=CAT).filter(thread=thread)
                    form = PostForm(request.POST or None)
                    if form.is_valid():
                        obj = form.save(commit=False)
                        obj.title = "noTitle"
                        obj.slug = slugify(obj.title)
                        obj.category = CAT
                        obj.thread = thread
                        obj.created_by = request.user
                        obj.created_on = datetime.datetime.now()
                        obj.save()
                        form = PostForm() 
                    return render(request, 'forum/post.html', {'ThreadName':thread.name, 'posts':posts, 'back':CAT.slug, 'form':form, 'catName':CAT.name})
        raise Http404   