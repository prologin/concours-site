import datetime
import re

from django.views import generic
from django.shortcuts import render, redirect
from django.utils.text import slugify
from django.http import Http404
from forum.models import Category, Post, Thread
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from forum.forms import PostForm, ThreadFrom, ThreadFromStaff

def replace_url_to_link(value):
    urls = re.compile(r"((https?):((//)|(\\\\))+[\w\d:#@%/;$()~_?\+-=\\\.&]*)", re.MULTILINE|re.UNICODE)
    value = urls.sub(r'<a href="\1" target="_blank">\1</a>', value)
    urls = re.compile(r"([\w\-\.]+@(\w[\w\-]+\.)+[\w\-]+)", re.MULTILINE|re.UNICODE)
    value = urls.sub(r'<a href="mailto:\1">\1</a>', value)
    return value

def home(request):
    cats = Category.objects.all()
    return render(request, 'forum/home.html', {'cats':cats})


def category(request, cat):
    cats = Category.objects.all()
    for CAT in cats:
        if cat.startswith(CAT.slug):
            threads = Thread.objects.all().filter(category=CAT, pin=False).order_by('-last_edited_on')
            pinThreads = Thread.objects.all().filter(category=CAT, pin=True).order_by('-last_edited_on')
            user = request.user
            if user.is_staff:
                formThread = ThreadFromStaff(request.POST or None)
            else:
                formThread = ThreadFrom(request.POST or None)
            formPost = PostForm(request.POST or None)
            if formThread.is_valid() & formPost.is_valid():
                new_thread = formThread.save(commit=False)
                new_post = formPost.save(commit=False)
                new_thread.slug = slugify(new_thread.name).replace('-', '')
                new_thread.category = CAT
                new_thread.created_by = request.user
                new_thread.last_edited_by = request.user
                new_thread.created_on = datetime.datetime.now()
                new_thread.last_edited_on = datetime.datetime.now()
                new_post.title = "noTitle"
                new_post.slug = slugify(new_post.title)
                new_post.category = CAT
                new_post.content = replace_url_to_link(new_post.content)
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
                return redirect(reverse('forum:home') + CAT.slug + '/' + new_thread.slug + '/1')
            return render(request, 'forum/threadList.html', {'cat_name':CAT.name, 'description':CAT.description, 'threads':threads, 'slug':CAT.slug, 'form_thread':formThread, 'form_post':formPost, 'nb_post':threads.count(), 'pin':pinThreads})
    raise Http404


def post(request, cat, pos, page):
    cats = Category.objects.all()
    for CAT in cats:
        if cat.startswith(CAT.slug):
            threads = Thread.objects.all().filter(category=CAT)
            thread = None
            for t in threads:
                if pos == t.slug:
                    thread = t
                    break
            if thread is None:
                raise Http404
            page_nb = int (page)
            posts = Post.objects.all().filter(category=CAT).filter(thread=thread)
            paginator = Paginator(posts, 10)
            form = PostForm(request.POST or None)
            if form.is_valid():
                if Post.objects.all().filter(category=CAT).filter(thread=thread).count() == (page_nb + 1) * 10:
                    page = str(page_nb + 1)
                obj = form.save(commit=False)
                obj.title = "noTitle"
                obj.slug = slugify(obj.title).replace('-', '')
                obj.category = CAT
                obj.thread = thread
                obj.content = replace_url_to_link(obj.content)
                obj.created_by = request.user
                obj.created_on = datetime.datetime.now()
                obj.save()
                thread.last_edited_by = request.user
                thread.last_edited_on = datetime.datetime.now()
                thread.save()
                CAT.nb_post = CAT.nb_post + 1
                CAT.last_edited_by = request.user
                CAT.last_edited_on = datetime.datetime.now()
                CAT.save()
                return redirect(reverse('forum:home') + CAT.slug + '/' + thread.slug + '/' + page)
            try:
                posts = paginator.page(page)
            except PageNotAnInteger:
                posts = paginator.page(1)
            except EmptyPage:
                posts = paginator.page(paginator.num_pages)
            return render(request, 'forum/post.html', {'thread_name':thread.name, 'posts':posts, 'url':CAT.slug, 'form':form, 'cat_name':CAT.name, 'page_nb':page_nb, 'thread_slug':thread.slug, 'max_page':paginator.num_pages})
    raise Http404
