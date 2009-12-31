# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
import os.path
import re
from datetime import datetime
from urllib2 import unquote
import json

from django.db.models import Q, Avg, Count
from django.contrib.auth.models import User
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from django.template import RequestContext
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
try:
    import simplejson as json
except ImportError:
    from django.utils import simplejson as json
from oxdjango.shortcuts import render_to_json_response
from oxdjango.decorators import login_required_json


import models
import utils
    
'''
field.length -> movie.sort.all()[0].field
o=0&n=100


a & b  | c & d

query

l=user:name or l=name
q=year:1980,hello,country:usa
q=year:1980,hello,country:!usa
q=title:^the$
q=title:^100%24$
q=year:<1970,year:>1960
q=year:<1960,year:>1950,title:sex

!1960-1970
2009.08.02.22.26.35-2009.08.02.22.26.35

!^the

 (dddd.dd.dd)-(dddd.dd.dd)

5-8
10000-20000

<2009-08-02-22-26-35

>2009-08-02-22-26-35
2009-08-02-22-26-35<

^the the*
*foo foo$
*foo* foo

s=director:asc,year:desc               default: director:asc,year:desc
r=0:100 or r=100 or r=100:             default: 0:100
p=id,title,director,date,cast.length   default: title,director,year,country
q

List data backend spec:
    url = //url for request
    params = [] //additional params passed to url, i.e. query, or group

the url must understand the following requests:
number of items:
    url?params&n=1
    > {items: N}
items sorted by key range X to Y:
    url?params&s=key:asc|desc&r=X:Y
    > {items: [{k0:v0, k1:v1...}, {k0:v0, k1:v1...}]}

Examples:
/json/find?l=all&s=title&f=all&q=&a=desc&p=id,title,director,date,cast.length

/json/find?r=0:100&l=all&s=title&f=all&q=&a=desc&p=id,title,director,date,cast.length
    {
        movies=[
            {
                "id":
                "title": "fsdf",
                "director":
            },
        ]
    }

#get sort order for all ids
/json/find?r=0:1000&l=all&s=title&f=all&q=&a=desc&p=id
    {
        movies=[
            {
                "id": id
            },
        ]
    }

/json/find?l=all&s=title&f=all&q=&a=desc
    {
        movies: 1234,
        files: 2345,
        pixels: 1242345345,
        size: 1235,
        duration: 1235,

    }

/json/find?r=0:100&l=all&s=[name, items]&f=all&q=&a=desc&g=country
    {
        groups = [ {name:"USA", movies: 123}, {name:"UK", movies: 1234} ]
    }

#find as you type: in table, by sort string

#auto compleat in find box

'''
def order_query(qs, s, prefix='sort__'):
    order_by = []
    for e in s.split(','):
        o = e.split(':')
        if len(o) == 1: o.append('asc')
        order = {'id': 'movieId'}.get(o[0], o[0])
        order = '%s%s' % (prefix, order)
        if o[1] == 'desc':
           order = '-%s' % order
        order_by.append(order)
    if order_by:
        qs = qs.order_by(*order_by)
    return qs

def parse_query(request):
    get = request.GET
    query = {}
    query['i'] = 0
    query['o'] = 100
    query['s'] = 'title:asc'
    def parse_dict(s):
        d = s.split(",")
        return [i.strip() for i in d]
    _dicts = ['p', ]
    _ints = ['n', ]
    for key in ('s', 'p', 'g', 'l', 'n'):
        if key in get:
            if key in _ints:
                query[key] = int(get[key])
            elif key in _dicts:
                query[key] = parse_dict(get[key])
            else:
                query[key] = get[key]
    query['q'] = models.Movie.objects.find(request)
    if 'r' in get:
        r = get['r'].split(':')
        if len(r) == 1: r.append(0)
        if r[0] == '': r[0] = 0
        if r[1] == '': r[0] = -1
        query['i'] = int(r[0])
        query['o'] = int(r[1])
    #group by only allows sorting by name or number of itmes
    return query

def find(request):
    query = parse_query(request)
    response = {}
    if 'p' in query:
        response['items'] = []
        qs = order_query(query['q'], query['s'])
        if 'n' in query:
            response = {'items': qs.count()}
        else:
            _p = query['p']
            def only_p(m):
                r = {}
                if m:
                    m = json.loads(m)
                    for p in _p:
                        r[p] = m[p]
                return r
            qs = qs[query['i']:query['o']]

            response['items'] = [only_p(m['json']) for m in qs.values('json')]

    elif 'g' in query:
        if query['s'].split(':')[0] not in ('name', 'items'):
            query['s'] = 'name'
        #FIXME: also filter lists here
        response['items'] = []
        name = 'name'
        items = 'movies'
        movie_qs = query['q']
        _objects = {
            'country': models.Country.objects,
            'genre': models.Genre.objects,
            'language': models.Language.objects,
            'director': models.Person.objects.filter(cast__role='directors'),
        }
        if query['g'] in _objects:
            qs = _objects[query['g']].filter(movies__id__in=movie_qs).values('name').annotate(movies=Count('movies'))
        elif query['g'] == "year":
            qs = movie_qs.values('imdb__year').annotate(movies=Count('id'))
            name='imdb__year'
        if 'n' in query:
            response['items'] = qs.count()
        else:
            #replace normalized items/name sort with actual db value
            order_by = query['s'].split(":")
            if len(order_by) == 1:
                order_by.append('desc')
            if order_by[0] == 'name':
                order_by = "%s:%s" % (name, order_by[1])
            else:
                order_by = "%s:%s" % (items, order_by[1])
            qs = order_query(qs, order_by, '')
            qs = qs[query['i']:query['o']]

            response['items'] = [{'title': i[name], 'items': i[items]} for i in qs]

    else:
        #FIXME: also filter lists here
        movies = models.Movie.objects.filter(available=True)
        files = models.File.objects.all()
        response['items'] = movies.count()
        response['files'] = files.count()
        r = files.aggregate(Count('size'), Count('pixels'), Count('duration'))
        response['pixels'] = r['pixels__count']
        response['size'] = r['size__count']
        response['duration'] = r['duration__count']
    return render_to_json_response(response)

'''
GET info?oshash=a41cde31c581e11d
    > {
        "movie_id": 0123456, ??
        "oshash": "a41cde31c581e11d",
        "sha1":..,
        "md5":..
        "duration": 5.266667,
        "video": [],
        "audio": [],
        "path": "E/Example, The/An Example.avi",
        "size": 1646274
      }
'''
def file_info(request):
    oshash = request.GET['oshash']
    f = models.MovieFile.objects.get(oshash=oshash)
    response = f.json()
    return render_to_json_response(response)


'''
GET subtitles?oshash=a41cde31c581e11d
  > {
    "languages": ['en', 'fr', 'de']
  }
GET subtitles?oshash=a41cde31c581e11d&language=en
    > srt file
POST subtitle?oshash=a41cde31c581e11d&language=en
srt =
'''
def subtitles(request):
    oshash = request.GET['oshash']
    language = request.GET.get('language', None)
    if request.method == 'POST':
        user = request.user
        sub = models.Subtitles.get_or_create(user, oshash, language)
        sub.srt = request.POST['srt']
        sub.save()
    else:
        if language:
            q = models.Subtitles.objects.filter(movie_file__oshash=oshash, language=language)
            if q.count() > 0:
                return HttpResponse(q[0].srt, content_type='text/x-srt')
        response = {}
        l = models.Subtitles.objects.filter(movie_file__oshash=oshash).values('language')
        response['languages'] = [f['language'] for f in l]
        return render_to_json_response(response)

'''
GET list
    > {
      "files": {
        "a41cde31c581e11d": {"path": "E/Example, The/An Example.avi", "size":1646274},
      }
    }
'''
@login_required_json
def list_files(request):
    response = {}
    response['files'] = {}
    qs = models.UserFile.filter(user=request.user)
    p = Paginator(qs, 1000)
    for i in p.page_range:
        page = p.page(i)
        for f in page.object_list:
              response['files'][f.movie_file.oshash] = {'path': f.path, 'size': f.movie_file.size}
    return render_to_json_response(response)

def find_files(request):
    response = {}
    query = parse_query(request)
    response['files'] = {}
    qs = models.UserFile.filter(user=request.user).filter(movie_file__movie__id__in=query['q'])
    p = Paginator(qs, 1000)
    for i in p.page_range:
        page = p.page(i)
        for f in page.object_list:
              response['files'][f.movie_file.oshash] = {'path': f.path, 'size': f.movie_file.size}
    return render_to_json_response(response)

'''
POST metadata
    > file: {
        "duration": 5.266667,
        "video_codec": "mpeg1",
        "pixel_format": "yuv420p",
        "width": 352,
        "height": 240,
        "pixel_aspect_ratio": "1:1",
        "display_aspect_ratio": "22:15",
        "framerate": "30:1",
        "audio_codec": "mp2",
        "samplerate": 44100,
        "channels": 1,
        "path": "E/Example, The/An Example.avi",
        "size": 1646274
        "oshash": "a41cde31c581e11d",
        "sha1":..,
        "md5":..
      }
'''
#@login_required_json
def add_metadata(request, archive):
    info = json.loads(request.POST['file'])
    oshash = info['oshash']
    archive = models.Archive.objects.get(name=archive)
    if archive.users.filter(user=request.user).count() == 1:
        user_file = models.ArchiveFile.get_or_create(archive, oshash)
        user_file.update(request.POST)
        response = {'status': 200}
    else:
        response = {'status': 404}
    return render_to_json_response(response)

class StillForm(forms.Form):
    still = forms.FileField()
    position = forms.FloatField()

#@login_required_json
def add_still(request, oshash):
    response = {'status': 500}
    f = get_object_or_404(models.File, oshash=oshash)

    form = TimelineForm(request.POST, request.FILES)
    if form.is_valid():
        ff = form.cleaned_data['still']
        position = form.cleaned_data['position']

        still = models.Still(file=f, position=position)
        still.save()
        still.still.save(ff, ff.name)
        response = {'status': 200}
        response['url'] = still.url()
    return render_to_json_response(response)

class TimelineForm(forms.Form):
    timeline = forms.FileField()

#FIXME: should everybody be able to overwrite timelines?
#@login_required_json
def add_timeline(request, oshash):
    response = {'status': 500}
    f = get_object_or_404(models.File, oshash=oshash)

    form = TimelineForm(request.POST, request.FILES)
    if form.is_valid():
        ff = form.cleaned_data['timeline']
        f.timeline.save(ff.name, ff)
        response = {'status': 200}
        response['url'] = f.timeline.url()
    return render_to_json_response(response)


class VideoForm(forms.Form):
    video = forms.FileField()

#@login_required_json
def add_video(request, oshash):
    response = {'status': 500}
    f = get_object_or_404(models.File, oshash=oshash)

    form = VideoForm(request.POST, request.FILES)
    if form.is_valid():
        ff = form.cleaned_data['video']
        f.stream128.save(ff.name, ff)
        response = {'status': 200}
        response['url'] = f.stream128.url()
    return render_to_json_response(response)

'''
POST update
    > files: {
        oshash: { 'path': .., ..},
        oshash: { 'path': .., ..},
      }
'''
#@login_required_json
def update_archive(request, archive):
    print "update request"
    archive = models.Archive.objects.get(name=archive)
    files = json.loads(request.POST['files'])
    print "update request for", archive.name
    needs_data = []
    rename = {}
    for oshash in files:
        print 'checking', oshash
        data = files[oshash]
        q = models.ArchiveFile.objects.filter(archive=archive, file__oshash=oshash)
        if q.count() == 0:
            print "adding file", oshash, data['path']
            f = models.ArchiveFile.get_or_create(archive, oshash)
            f.update(data)
            #FIXME: only add if it was not in File
        else:
            f = q[0]
            if data['path'] != f.path:
                f.path = data['path']
                f.save()
        if f.file.needs_data:
            needs_data.append(oshash)
        if f.path != f.file.path:
            rename[oshash] = f.file.path
    print "processed files for", archive.name
    #remove all files not in files.keys() from ArchiveFile
    response = {}
    response['info'] = needs_data
    response['rename'] = rename
    return render_to_json_response(response)

def file_parse(request):
    response = utils.parsePath(request.POST['path'])
    return render_to_json_response(response)


