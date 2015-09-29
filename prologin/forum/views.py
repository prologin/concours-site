import datetime

from django.views import generic
from django.shortcuts import render, redirect
from django.utils.text import slugify
from django.http import Http404
from forum.models import Category, Post, Thread


from forum.forms import PostForm, ThreadFrom


def home(request):
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
                        new_thread.nb_post = 1
                        new_post.title = "noTitle"
                        new_post.slug = slugify(new_post.title)
                        new_post.category = CAT
                        new_post.created_by = request.user
                        new_post.created_on = datetime.datetime.now()
                        new_thread.save()
                        new_post.thread = new_thread
                        new_post.save()
                        CAT.nb_thread = CAT.nb_thread + 1
                        CAT.nb_post = CAT.nb_post + 1
                        CAT.last_edited_by = request.user
                        CAT.last_edited_on = datetime.datetime.now()
                        CAT.save()
                        return redirect('/forum/' + CAT.slug + '/' + new_thread.slug)
                    return render(request, 'forum/threadList.html', {'cat_name':CAT.name, 'description':CAT.description, 'threads':threads, 'slug':CAT.slug, 'form_thread':formThread, 'form_post':formPost})
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
                        thread.last_edited_by = request.user
                        thread.last_edited_on = datetime.datetime.now()
                        thread.nb_post = thread.nb_post + 1
                        thread.save()
                        CAT.nb_post = CAT.nb_post + 1
                        CAT.last_edited_by = request.user
                        CAT.last_edited_on = datetime.datetime.now()
                        CAT.save()
                        return redirect('/forum/' + CAT.slug + '/' + thread.slug)
                    return render(request, 'forum/post.html', {'thread_name':thread.name, 'posts':posts, 'url':CAT.slug, 'form':form, 'cat_name':CAT.name})
        raise Http404