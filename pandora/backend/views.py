# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division
import os.path
import re
from datetime import datetime
from urllib2 import unquote
import mimetypes

from django import forms
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q, Avg, Count, Sum
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from django.template import RequestContext
from django.conf import settings

try:
    import simplejson as json
except ImportError:
    from django.utils import simplejson as json

from oxdjango.decorators import login_required_json
from oxdjango.shortcuts import render_to_json_response, get_object_or_404_json, json_response
from oxdjango.http import HttpFileResponse
import ox

import models
import utils
import tasks

from oxuser.models import getUserJSON
from oxuser.views import api_login, api_logout, api_register, api_contact, api_recover, api_preferences
from archive.views import api_update, api_addArchive, api_editArchive, api_removeArchive

from archive.models import File

def api(request):
    if request.META['REQUEST_METHOD'] == "OPTIONS":
        response = HttpResponse('')
        response = render_to_json_response({'status': {'code': 200, 'text': 'use POST'}})
        response['Access-Control-Allow-Origin'] = '*'
        return response
    if not 'action' in request.POST:
        return apidoc(request)
    function = request.POST['action']
    #FIXME: possible to do this in f
    #data = json.loads(request.POST['data'])

    #FIXME: security considerations, web facing api should not call anything in globals!!!
    f = globals().get('api_'+function, None)
    if f:
        response = f(request)
    else:
        response = render_to_json_response(json_response(status=400,
                                text='Unknown function %s' % function))
    response['Access-Control-Allow-Origin'] = '*'
    return response

def api_hello(request):
    '''
        return {'status': {'code': int, 'text': string},
                'data': {user: object}}
    '''
    response = json_response({})
    if request.user.is_authenticated():
        response['data']['user'] = getUserJSON(request.user)
    else:
        response['data']['user'] = {'name': 'Guest', 'group': 'guest', 'preferences': {}}
    return render_to_json_response(response)

def api_error(request):
    '''
        trows 503 error
    '''
    success = error_is_success
    return render_to_json_response({})

def _order_query(qs, sort, prefix='sort__'):
    order_by = []
    if len(sort) == 1:
        if sort[0]['key'] in ('title', 'director'):
            sort.append({'operator': '-', 'key': 'year'})
        if sort[0]['key'] in ('year', ):
            sort.append({'operator': '+', 'key': 'director'})
    for e in sort:
        operator = e['operator']
        if operator != '-': operator = ''
        key = {'id': 'movieId'}.get(e['key'], e['key'])
        #FIXME: this should be a property of models.MovieSort!!!
        if operator=='-' and key in ('title', 'director', 'writer', 'producer', 'editor', 'cinematographer', 'language', 'country', 'year'):
            key = '%s_desc' % key
        order = '%s%s%s' % (operator, prefix, key)
        order_by.append(order)
    if order_by:
        qs = qs.order_by(*order_by)
    return qs

def _parse_query(data, user):
    query = {}
    query['range'] = [0, 100]
    query['sort'] = [{'key':'title', 'operator':'+'}]
    for key in ('sort', 'keys', 'group', 'list', 'range', 'ids'):
        if key in data:
            query[key] = data[key]
    query['qs'] = models.Movie.objects.find(data, user)
    #group by only allows sorting by name or number of itmes
    return query

def _get_positions(ids, get_ids):
    positions = {}
    for i in get_ids:
        try:
            positions[i] = ids.index(i)
        except:
            pass
    return positions

def api_find(request):
    '''
        param data
            {'query': query, 'sort': array, 'range': array}
        
            query: query object, more on query syntax at
                   https://wiki.0x2620.org/wiki/pandora/QuerySyntax
            sort: array of key, operator dics
                [
                    {
                        key: "year",
                        operator: "-"
                    },
                    {
                        key: "director",
                        operator: ""
                    }
                ]
            range:       result range, array [from, to]
            keys:  array of keys to return
            group:    group elements by, country, genre, director...

        with keys, items is list of dicts with requested properties:
          return {'status': {'code': int, 'text': string},
                'data': {items: array}}

Groups
        param data
            {'query': query, 'key': string, 'group': string, 'range': array}
        
            query: query object, more on query syntax at
                   https://wiki.0x2620.org/wiki/pandora/QuerySyntax
            range:       result range, array [from, to]
            keys:  array of keys to return
            group:    group elements by, country, genre, director...

        possible values for keys: name, items

        with keys
        items contains list of {'name': string, 'items': int}:
        return {'status': {'code': int, 'text': string},
            'data': {items: array}}

        without keys: return number of items in given query
          return {'status': {'code': int, 'text': string},
                'data': {items: int}}

Positions
        param data
            {'query': query, 'ids': []}
        
            query: query object, more on query syntax at
                   https://wiki.0x2620.org/wiki/pandora/QuerySyntax
            ids:  ids of items for which positions are required
    '''
    data = json.loads(request.POST['data'])
    if settings.JSON_DEBUG:
        print json.dumps(data, indent=2)
    query = _parse_query(data, request.user)
    
    response = json_response({})
    if 'group' in query:
        if 'sort' in query:
            if len(query['sort']) == 1 and query['sort'][0]['key'] == 'items':
                if query['group'] == "year":
                    query['sort'].append({'key': 'name', 'operator':'-'})
                else:
                    query['sort'].append({'key': 'name', 'operator':'+'})
        else:
            query['sort'] = [{'key': 'name', 'operator':'+'}]
        #FIXME: also filter lists here
        response['data']['items'] = []
        items = 'movies'
        movie_qs = query['qs']
        qs = models.Facet.objects.filter(key=query['group']).filter(movie__id__in=movie_qs)
        qs = qs.values('value').annotate(movies=Count('id')).order_by()
        name = 'value'
        name_sort = 'value_sort'

        #replace normalized items/name sort with actual db value
        for i in range(0, len(query['sort'])):
            if query['sort'][i]['key'] == 'name':
                query['sort'][i]['key'] = name_sort
            elif query['sort'][i]['key'] == 'items':
                query['sort'][i]['key'] = items
        qs = _order_query(qs, query['sort'], prefix='')
        if 'ids' in query:
            #FIXME: this does not scale for larger results
            response['data']['positions'] = {}
            ids = [j[name] for j in qs]
            response['data']['positions'] = _get_positions(ids, query['ids'])

        elif 'range' in data:
            qs = qs[query['range'][0]:query['range'][1]]
            if name == 'year':
                response['data']['items'] = [{'name': i.year, 'items': i.movies} for i in qs]
            else:
                response['data']['items'] = [{'name': i[name], 'items': i[items]} for i in qs]
        else:
            response['data']['items'] = qs.count()
    elif 'ids' in query:
        #FIXME: this does not scale for larger results
        qs = _order_query(query['qs'], query['sort'])
        
        response['data']['positions'] = {}
        ids = [j['movieId'] for j in qs.values('movieId')]
        response['data']['positions'] = _get_positions(ids, query['ids'])

    elif 'keys' in query:
        response['data']['items'] = []
        qs = _order_query(query['qs'], query['sort'])
        _p = query['keys']
        def only_p(m):
            r = {}
            if m:
                m = json.loads(m)
                for p in _p:
                    r[p] = m.get(p, '')
            return r
        qs = qs[query['range'][0]:query['range'][1]]
        response['data']['items'] = [only_p(m['json']) for m in qs.values('json')]
    else: # otherwise stats
        #movies = models.Movie.objects.filter(available=True)
        movies = query['qs']
        files = File.objects.all().filter(movie__in=movies)
        r = files.aggregate(
            Sum('duration'),
            Sum('pixels'),
            Sum('size')
        )
        response['data']['duration'] = r['duration__sum']
        response['data']['files'] = files.count()
        response['data']['items'] = movies.count()
        response['data']['pixels'] = r['pixels__sum']
        response['data']['runtime'] = movies.aggregate(Sum('sort__runtime'))['sort__runtime__sum']
        if response['data']['runtime'] == None:
            response['data']['runtime'] = 1337
        response['data']['size'] = r['size__sum']
    return render_to_json_response(response)

def api_getItem(request):
    '''
        param data
            string id

		return item array
    '''
    response = json_response({})
    itemId = json.loads(request.POST['data'])
    item = get_object_or_404_json(models.Movie, movieId=itemId)
	#FIXME: check permissions
	response['data'] = {'item': item.json}
    return render_to_json_response(response)

@login_required_json
def api_editItem(request):
    '''
        param data
            {id: string, key: value,..}
        return {'status': {'code': int, 'text': string},
                'data': {}}
    '''
    data = json.loads(request.POST['data'])
    item = get_object_or_404_json(models.Movie, movieId=data['id'])
    if item.editable(request.user):
        response = json_response(status=501, text='not implemented')
		item.edit(data)
	else:
        response = json_response(status=403, text='permissino denied')
    return render_to_json_response(response)

@login_required_json
def api_removeItem(request):
    '''
        param data
            string id

        return {'status': {'code': int, 'text': string}}
    '''
    response = json_response({})
    itemId = json.loads(request.POST['data'])
    item = get_object_or_404_json(models.Movie, movieId=itemId)
	if item.editable(request.user):
        response = json_response(status=501, text='not implemented')
	else:
        response = json_response(status=403, text='permissino denied')
    return render_to_json_response(response)

@login_required_json
def api_addLayer(request):
    '''
        param data
            {key: value}
        return {'status': {'code': int, 'text': string},
                'data': {}}
    '''
    response = {'status': {'code': 501, 'text': 'not implemented'}}
    return render_to_json_response(response)

@login_required_json
def api_removeLayer(request):
    '''
        param data
            {key: value}
        return {'status': {'code': int, 'text': string},
                'data': {}}
    '''
    response = {'status': {'code': 501, 'text': 'not implemented'}}
    return render_to_json_response(response)

@login_required_json
def api_editLayer(request):
    '''
        param data
            {key: value}
        return {'status': {'code': int, 'text': string},
                'data': {}}
    '''
    response = json_response({})
    data = json.loads(request.POST['data'])
    layer = get_object_or_404_json(models.Layer, pk=data['id'])
	if layer.editable(request.user):
		response = json_response(status=501, text='not implemented')
	else:
		response = json_response(status=403, text='permission denied')
    return render_to_json_response(response)

    response = json_response(status=501, text='not implemented')
    return render_to_json_response(response)

@login_required_json
def api_addListItem(request):
    '''
        param data
            {key: value}
        return {'status': {'code': int, 'text': string},
                'data': {}}
    '''
    response = json_response(status=501, text='not implemented')
    return render_to_json_response(response)

@login_required_json
def api_removeListItem(request):
    '''
        param data
            {key: value}
        return {'status': {'code': int, 'text': string},
                'data': {}}
    '''
    response = json_response(status=501, text='not implemented')
    return render_to_json_response(response)

@login_required_json
def api_addList(request):
    '''
        param data
            {key: value}
        return {'status': {'code': int, 'text': string},
                'data': {}}
    '''
    response = json_response(status=501, text='not implemented')
    return render_to_json_response(response)

@login_required_json
def api_editList(request):
    '''
        param data
            {key: value}
        return {'status': {'code': int, 'text': string},
                'data': {}}
    '''
    response = json_response(status=501, text='not implemented')
    return render_to_json_response(response)

def api_removeList(request):
    '''
        param data
            {key: value}
        return {'status': {'code': int, 'text': string},
                'data': {}}
    '''
    response = json_response(status=501, text='not implemented')
    return render_to_json_response(response)

def api_encodingSettings(request):
    '''
        returns Firefogg encoding settings as specified by site
        return {'status': {'code': int, 'text': string},
                'data': {'options': {'videoQuality':...}}}
    '''
    response = json_response({'options': settings.VIDEO_ENCODING[settings.VIDEO_PROFILE]})
    return render_to_json_response(response)

class UploadForm(forms.Form):
    data = forms.TextInput()
    file = forms.FileField()

class VideoChunkForm(forms.Form):
    chunk = forms.FileField()
    done = forms.IntegerField(required=False)

@login_required_json
def api_upload(request): #video, timeline, frame
    '''
        upload video, timeline or frame
        param data
        param file
        return {'status': {'code': int, 'text': string},
                'data': {}}
    '''
    form = UploadForm(request.POST, request.FILES)
    if form.is_valid():
        data = json.loads(request.POST['data'])
        oshash = data['oshash']
        f = get_object_or_404(models.File, oshash=oshash)
        if data['item'] == 'frame':
            ff = form.cleaned_data['file']
            position = data['position']
            frame, created = models.Frame.objects.get_or_create(file=f, position=position)
            if not created and frame.frame:
                frame.frame.delete()
            frame.frame.save(ff.name, ff)
            frame.save()
            response = json_response({'url': frame.frame.url})
            return render_to_json_response(response)
        if data['item'] == 'timeline':
            pass
            #print "not implemented"

    response = json_response(status=501, text='not implemented')
    return render_to_json_response(response)

@login_required_json
def firefogg_upload(request):
    #handle video upload
    if request.method == 'POST':
        #init upload
        if 'oshash' in request.POST:
            #FIXME: what to do if requested oshash is not in db?
            #FIXME: should existing data be reset here? or better, should this fail if an upload was there
            f = get_object_or_404(models.File, oshash=request.POST['oshash'])
            stream = getattr(f, 'stream_%s'%settings.VIDEO_UPLOAD)
            if stream:
                stream.delete()
            f.available = False
            f.save()
            response = {
                'uploadUrl': request.build_absolute_uri('/api/upload/?oshash=%s' % f.oshash),
                'result': 1
            }
            return render_to_json_response(response)
        #post next chunk
        if 'chunk' in request.FILES and 'oshash' in request.GET:
            print "all chunk now"
            f = get_object_or_404(models.File, oshash=request.GET['oshash'])
            form = VideoChunkForm(request.POST, request.FILES)
            #FIXME: 
            if form.is_valid() and f.editable(request.user):
                c = form.cleaned_data['chunk']
                response = {
                    'result': 1,
                    'resultUrl': request.build_absolute_uri('/')
                }
                if not f.save_chunk(c, c.name):
                    response['result'] = -1
                elif form.cleaned_data['done']:
                    #FIXME: send message to encode deamon to create derivates instead
                    f.available = True
                    f.save()
                    response['result'] = 1
                    response['done'] = 1
                return render_to_json_response(response)
    print request.GET, request.POST
    response = json_response(status=400, text='this request requires POST')
    return render_to_json_response(response)

@login_required_json
def api_editFile(request): #FIXME: should this be file.files. or part of update
    '''
        change file / imdb link
    '''
    response = json_response(status=501, text='not implemented')
    return render_to_json_response(response)

def api_parse(request): #parse path and return info
    '''
        param data
            {path: string}
        return {'status': {'code': int, 'text': string},
                data: {imdb: string}}
    '''
    path = json.loads(request.POST['data'])['path']
    response = json_response(utils.parsePath(path))
    return render_to_json_response(response)

def api_getImdbId(request):
    '''
        param data
            {title: string, director: string, year: string}
        return {'status': {'code': int, 'text': string},
                'data': {imdbId:string }}
    '''
    imdbId = ox.web.imdb.guess(search_title, r['director'], timeout=-1)
    if imdbId:
        response = json_response({'imdbId': imdbId})
    else:
		response = json_response(status=404, text='not found')
    return render_to_json_response(response)

def api_fileInfo(request):
    '''
        param data
            oshash string
        return {'status': {'code': int, 'text': string},
                'data': {imdbId:string }}
    '''
    if 'data' in request.POST:
		oshash = json.loads(request.POST['data'])
	elif 'oshash' in request.GET:
		oshash = request.GET['oshash']
    f = models.MovieFile.objects.get(oshash=oshash)
    response = {'data': f.json()}
    return render_to_json_response(response)

def api_subtitles(request):
	'''
	param data
		oshash string
		language string
		subtitle string
	return
		if no language is provided:
			{data: {languages: array}}
		if language is set:
			{data: {subtitle: string}}
		if subtitle is set:
			saves subtitle for given language
	'''
    if 'data' in request.POST:
		data = json.loads(request.POST['data'])
		oshash = data['oshash']
		language = data.get('language', None)
		srt = data.get('subtitle', None)
	if srt:
        user = request.user
        sub = models.Subtitles.objects.get_or_create(user, oshash, language)
        sub.srt = srt
        sub.save()
    else:
        response = json_response({})
        if language:
            q = models.Subtitles.objects.filter(movie_file__oshash=oshash, language=language)
            if q.count() > 0:
				response['data']['subtitle'] = q[0].srt
				return render_to_json_response(response)
        l = models.Subtitles.objects.filter(movie_file__oshash=oshash).values('language')
        response['data']['languages'] = [f['language'] for f in l]
        return render_to_json_response(response)
    
def video(request, id, quality):
    movie = get_object_or_404(models.Movie, movieId=id)
    if quality not in settings.VIDEO_ENCODING:
        raise Http404
    stream = getattr(movie, 'stream_'+quality)
    response = HttpFileResponse(stream.path, content_type='video/ogg')
    #FIXME: movie needs duration field
    #response['Content-Duration'] = movie.duration
    return response

def frame(request, id, position, size):
    movie = get_object_or_404(models.Movie, movieId=id)
    position = ox.time2ms(position)/1000
    frame = movie.frame(position, int(size))
    if not frame:
        raise Http404
    return HttpFileResponse(frame, content_type='image/jpeg')

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
    query = _parse_query(request)
    response['files'] = {}
    qs = models.UserFile.filter(user=request.user).filter(movie_file__movie__id__in=query['q'])
    p = Paginator(qs, 1000)
    for i in p.page_range:
        page = p.page(i)
        for f in page.object_list:
              response['files'][f.movie_file.oshash] = {'path': f.path, 'size': f.movie_file.size}
    return render_to_json_response(response)


def apidoc(request):
    '''
        this is used for online documentation at http://127.0.0.1:8000/api/
    '''
    import sys
    def trim(docstring):
        if not docstring:
            return ''
        # Convert tabs to spaces (following the normal Python rules)
        # and split into a list of lines:
        lines = docstring.expandtabs().splitlines()
        # Determine minimum indentation (first line doesn't count):
        indent = sys.maxint
        for line in lines[1:]:
            stripped = line.lstrip()
            if stripped:
                indent = min(indent, len(line) - len(stripped))
        # Remove indentation (first line is special):
        trimmed = [lines[0].strip()]
        if indent < sys.maxint:
            for line in lines[1:]:
                trimmed.append(line[indent:].rstrip())
        # Strip off trailing and leading blank lines:
        while trimmed and not trimmed[-1]:
            trimmed.pop()
        while trimmed and not trimmed[0]:
            trimmed.pop(0)
        # Return a single string:
        return '\n'.join(trimmed)

    functions = filter(lambda x: x.startswith('api_'), globals().keys())
    api = []
    for f in sorted(functions):
        api.append({
            'name': f[4:],
            'doc': trim(globals()[f].__doc__).replace('\n', '<br>\n')
        })
    context = RequestContext(request, {'api': api,
                                       'sitename': settings.SITENAME,})
    return render_to_response('api.html', context)
