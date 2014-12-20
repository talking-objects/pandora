# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division
import os.path
import mimetypes
import random
from urlparse import urlparse
from urllib import quote
import time

import Image
from django.db.models import Count, Sum
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseForbidden, Http404
from django.shortcuts import get_object_or_404, redirect, render_to_response
from django.core.files.temp import NamedTemporaryFile
from django.core.servers.basehttp import FileWrapper
from django.conf import settings

from ox.utils import json, ET

from ox.django.decorators import login_required_json
from ox.django.shortcuts import render_to_json_response, get_object_or_404_json, json_response
from ox.django.http import HttpFileResponse
import ox

import models
import utils
import tasks

from archive.models import File, Stream
from archive import extract
from clip.models import Clip 
from user.models import has_capability
from changelog.models import add_changelog

from ox.django.api import actions


def _order_query(qs, sort, prefix='sort__'):
    order_by = []
    if len(sort) == 1:
        additional_sort = settings.CONFIG['user']['ui']['listSort']
        key = utils.get_by_id(settings.CONFIG['itemKeys'], sort[0]['key'])
        for s in key.get('additionalSort', additional_sort):
            sort.append(s)
    for e in sort:
        operator = e['operator']
        if operator != '-':
            operator = ''
        key = {
            'id': 'public_id',
            'index': 'listitem__index'
        }.get(e['key'], e['key'])
        if key not in ('listitem__index', ):
            key = "%s%s" % (prefix, key)
        order = '%s%s' % (operator, key)
        order_by.append(order)
    if order_by:
        qs = qs.order_by(*order_by, nulls_last=True)
    return qs

def _order_by_group(query):
    if 'sort' in query:
        if len(query['sort']) == 1 and query['sort'][0]['key'] == 'items':
            order_by = query['sort'][0]['operator'] == '-' and '-items' or 'items'
            if query['group'] == "year":
                secondary = query['sort'][0]['operator'] == '-' and '-sortvalue' or 'sortvalue'
                order_by = (order_by, secondary)
            elif query['group'] != "keyword":
                order_by = (order_by, 'sortvalue')
            else:
                order_by = (order_by, 'value')
        else:
            order_by = query['sort'][0]['operator'] == '-' and '-sortvalue' or 'sortvalue'
            order_by = (order_by, 'items')
    else:
        order_by = ('-sortvalue', 'items')
    return order_by

def parse_query(data, user):
    query = {}
    query['range'] = [0, 100]
    query['sort'] = [{'key':'title', 'operator':'+'}]
    for key in ('sort', 'keys', 'group', 'range', 'position', 'positions'):
        if key in data:
            query[key] = data[key]
    query['qs'] = models.Item.objects.find(data, user)
    if 'clips' in data:
        conditions = {'query': data['clips']['query']}
        query['clip_qs'] = Clip.objects.find(conditions, user).order_by('start')
        query['clip_filter'] = models.Clip.objects.filter_annotations(conditions, user)
        query['clip_items'] = data['clips'].get('items', 5)
        query['clip_keys'] = data['clips'].get('keys')
        if not query['clip_keys']:
            query['clip_keys'] = ['id', 'in', 'out', 'annotations']

    #group by only allows sorting by name or number of itmes
    return query

def find(request, data):
    '''
    Finds items for a given query
    takes {
        clipsQuery: object, // clips query object (optional)
        group: string, // item key to group results by (optional)
        keys: [string], // list of keys to return, [] for all (optional)
        positions: [string], // list of item ids (optional)
        query: { // query object
            conditions: [{ // list of condition objects...
                key: string, // item key
                operator: string, // comparison operator, see below
                value: string // value
            }, { // ... and/or query objects (nested subconditions)
                query: {
                    conditions: [object, ...], // list of condition objects
                    operator: string // logical operator, '&' or '|'
                }
            }],
            operator: string // logical operator, '&' or '|'
        },
        range: [int, int] // items to return, per current sort order
        sort: [{ // list of sort objects, applied in the given ordering
            key: string, // item key
            operator: string // sort operator, '+' or '-'
        }]
    }
    returns { // if `keys` is present
        items: [ // returns list of matching items
            {
                id: string, // item id
                ... // more item properties
            },
            ... // more items
        ]
    } or { // if `clipsQuery` is present
        clips: [ // returns list of matching clips
            {
                id: string, // clip id
                ... // more clip properties
            },
            ... // more clips
        ]
    } or { // if `group` is present
        items: [ // returns results for filters
            {
                name: string, // value for item key specified as group
                items: int // number of matches
            },
            ... // more group objects
        ]
    } or { // if `keys` is missing
        items: int // returns total number of items
    } or { // if `positions` is present
        positions: { // returns positions of given items
            id: position, // position of the item, per current sort order
            ... // more id/position pairs
        }
    }
    notes: Comparison operators are '=' (contains) '==' (is), '^' (starts with),
    '$' (ends with), '<', '<=', '>', or '>=', each optionally prefixed with '!'
    (not).
    Leaving out `keys` or passing `positions` can be useful when building a
    responsive UI: First leave out `keys` to get totals as fast as possible,
    then pass `positions` to get the positions of previously selected items,
    finally make the query with `keys` and an appropriate range.
    For more examples, see https://wiki.0x2620.org/wiki/pandora/QuerySyntax.
    see: add, edit, get, lookup, remove, upload
    '''
    if settings.JSON_DEBUG:
        print json.dumps(data, indent=2)
    query = parse_query(data, request.user)

    response = json_response({})
    if 'group' in query:
        response['data']['items'] = []
        items = 'items'
        item_qs = query['qs']
        order_by = _order_by_group(query)
        qs = models.Facet.objects.filter(key=query['group']).filter(item__id__in=item_qs)
        qs = qs.values('value').annotate(items=Count('id')).order_by(*order_by)

        if 'positions' in query:
            response['data']['positions'] = {}
            ids = [j['value'] for j in qs]
            response['data']['positions'] = utils.get_positions(ids, query['positions'])
        elif 'range' in data:
            qs = qs[query['range'][0]:query['range'][1]]
            response['data']['items'] = [{'name': i['value'], 'items': i[items]} for i in qs]
        else:
            response['data']['items'] = qs.count()
    elif 'position' in query:
        qs = _order_query(query['qs'], query['sort'])
        ids = [j['public_id'] for j in qs.values('public_id')]
        data['conditions'] = data['conditions'] + {
            'value': query['position'],
            'key': query['sort'][0]['key'],
            'operator': '^'
        }
        query = parse_query(data, request.user)
        qs = _order_query(query['qs'], query['sort'])
        if qs.count() > 0:
            response['data']['position'] = utils.get_positions(ids, [qs[0].public_id])[0]
    elif 'positions' in query:
        qs = _order_query(query['qs'], query['sort'])
        ids = [j['public_id'] for j in qs.values('public_id')]
        response['data']['positions'] = utils.get_positions(ids, query['positions'])
    elif 'keys' in query:
        response['data']['items'] = []
        qs = _order_query(query['qs'], query['sort'])
        _p = query['keys']

        def get_clips(qs):
            n = qs.count()
            if n > query['clip_items']:
                num = query['clip_items']
                clips = []
                step = int(n / (num + 1))
                i = step
                while i <= (n - step) and i < n and len(clips) < num:
                    clips.append(qs[i])
                    i += step
            else:
                clips = qs
            return [c.json(query['clip_keys'], query['clip_filter']) for c in clips]

        def only_p_sums(m):
            r = {}
            for p in _p:
                if p  == 'accessed':
                    r[p] = m.sort.accessed or ''
                elif p == 'modified':
                    r[p] = m.sort.modified
                elif p == 'timesaccessed':
                    r[p] = m.sort.timesaccessed
                else:
                    r[p] = m.json.get(p, '')
            if 'clip_qs' in query:
                r['clips'] = get_clips(query['clip_qs'].filter(item=m))
            return r
        def only_p(m):
            r = {}
            if m:
                m = json.loads(m, object_hook=ox.django.fields.from_json)
                for p in _p:
                    r[p] = m.get(p, '')
            if 'clip_qs' in query:
                r['clips'] = get_clips(query['clip_qs'].filter(item__public_id=m['id']))
            return r
        qs = qs[query['range'][0]:query['range'][1]]
        #response['data']['items'] = [m.get_json(_p) for m in qs]
        if filter(lambda p: p in (
            'accessed', 'modified', 'timesaccessed', 'viewed'
        ), _p):
            qs = qs.select_related()
            response['data']['items'] = [only_p_sums(m) for m in qs]
        else:
            response['data']['items'] = [only_p(m['json']) for m in qs.values('json')]

    else: # otherwise stats
        items = query['qs']
        files = File.objects.filter(item__in=items).filter(selected=True).filter(size__gt=0)
        r = files.aggregate(
            Sum('duration'),
            Sum('pixels'),
            Sum('size')
        )
        totals = [i['id']
            for i in settings.CONFIG['totals']
            if not 'capability' in i or has_capability(request.user, i['capability'])
        ]
        if 'duration' in totals:
            response['data']['duration'] = r['duration__sum']
        if 'files' in totals:
            response['data']['files'] = files.count()
        if 'items' in totals:
            response['data']['items'] = items.count()
        if 'pixels' in totals:
            response['data']['pixels'] = r['pixels__sum']
        if 'runtime' in totals:
            response['data']['runtime'] = items.aggregate(Sum('sort__runtime'))['sort__runtime__sum'] or 0
        if 'size' in totals:
            response['data']['size'] = r['size__sum']
        for key in ('runtime', 'duration', 'pixels', 'size'):
            if key in totals and response['data'][key] == None:
                response['data'][key] = 0 
    return render_to_json_response(response)
actions.register(find)


def autocomplete(request, data):
    '''
    Returns autocomplete strings for a given item key and search string
    takes {
        key: string, // item key
        value: string, // search string
        operator: string, // '=', '==', '^', '$'
        query: object, // item query to limit results, see `find`
        range: [int, int] // range of tesults to return
    }
    returns {
        items: [string, ...] // list of matching strings
    }
    see: autocompleteEntities
    '''
    if not 'range' in data:
        data['range'] = [0, 10]
    op = data.get('operator', '=')

    key = utils.get_by_id(settings.CONFIG['itemKeys'], data['key'])
    order_by = key.get('autocompleteSort', False)
    if order_by:
        for o in order_by:
            if o['operator'] != '-': o['operator'] = '' 
        order_by = ','.join(['%(operator)ssort__%(key)s' % o for o in order_by])
    else:
        order_by = '-items'
    sort_type = key.get('sortType', key.get('type', 'string'))
    if sort_type == 'title':
        qs = parse_query({'query': data.get('query', {})}, request.user)['qs']
        if data['value']:
            if op == '=':
                qs = qs.filter(find__key=data['key'], find__value__icontains=data['value'])
            elif op == '==':
                qs = qs.filter(find__key=data['key'], find__value__iexact=data['value'])
            elif op == '^':
                qs = qs.filter(find__key=data['key'], find__value__istartswith=data['value'])
            elif op == '$':
                qs = qs.filter(find__key=data['key'], find__value__iendswith=data['value'])
        qs = qs.order_by(order_by, nulls_last=True)
        qs = qs[data['range'][0]:data['range'][1]]
        response = json_response({})
        response['data']['items'] = list(set([i.get(data['key']) for i in qs]))
    else:
        qs = models.Facet.objects.filter(key=data['key'])
        if data['value']:
            if op == '=':
                qs = qs.filter(value__icontains=data['value'])
            elif op == '==':
                qs = qs.filter(value__iexact=data['value'])
            elif op == '^':
                qs = qs.filter(value__istartswith=data['value'])
            elif op == '$':
                qs = qs.filter(value__iendswith=data['value'])
        if 'query' in data:
            item_query = parse_query({'query': data.get('query', {})}, request.user)['qs']
            qs = qs.filter(item__in=item_query)
        qs = qs.values('value').annotate(items=Count('id'))
        qs = qs.order_by(order_by)
        qs = qs[data['range'][0]:data['range'][1]]
        response = json_response({})
        response['data']['items'] = [i['value'] for i in qs]
    return render_to_json_response(response)
actions.register(autocomplete)

def findId(request, data):
    '''
    Undocumented
    takes {
        id: string
        title: string
        director: [string]
        year: int
    }
    '''
    response = json_response({})
    response['data']['items'] = []
    if 'id' in data:
        qs = models.Item.objects.filter(public_id=data['id'])
        if qs.count() == 1:
            response['data']['items'] = [
                i.get_json(['title', 'director', 'year', 'id']) for i in qs
            ]

    if not response['data']['items'] \
        and settings.USE_IMDB \
        and settings.DATA_SERVICE:
        r = models.external_data('getId', data)
        if r['status']['code'] == 200:
            response['data']['items'] = [r['data']]
    return render_to_json_response(response)
actions.register(findId)


def getMetadata(request, data):
    '''
    Gets metadata from an external service
    takes {
        id: string, // item id
        keys: [string] // list of item keys to return
    }
    returns {
       key: value // item key and value
       ... // more key/value pairs
    }
    notes: This can be used to populate metadata from a remote source, like
    IMDb.
    see: getIds, updateExternalData
    '''
    response = json_response({})
    if settings.DATA_SERVICE:
        '''
        info = {}
        for c in data['query']['conditions']:
            info[c['key']] = c['value']
        r = models.external_data('getId', info)
        '''
        r = models.external_data('getData', {'id': data['id']})
        if r['status']['code'] == 200:
            if 'keys' in data and data['keys']:
                for key in data['keys']:
                    if key in r['data']:
                        response['data'][key] = r['data'][key]
            else:
                response['data'] = r['data']
    return render_to_json_response(response)
actions.register(getMetadata)

def getIds(request, data):
    '''
    Gets ids from an external service
    takes {
        title: string, // title
        director: [string], // list of directors
        year: int // year
    }
    returns {
        items: [{
            title: string, // title
            director: [string], // list of directors
            year: int, // year
            originalTitle: string // original title
        }]
    }
    notes: This can be used to populate metadata from a remote source, like
    IMDb.
    see: getMetadata, updateExternalData
    '''
    response = json_response({})
    if settings.DATA_SERVICE:
        r = models.external_data('getIds', data)
        if r['status']['code'] == 200:
            response['data']['items'] = r['data']['items']
    else:
        response['data']['items']
    return render_to_json_response(response)
actions.register(getIds)

def get(request, data):
    '''
    Gets an item by id
    takes {
        id: string, // item id
        keys: [string] // item properties to return
    }
    returns {
        key: value, // item key and value
        ... // more key/value pairs
    }
    see: add, edit, find, lookup, remove, upload
    '''
    response = json_response({})
    data['keys'] = data.get('keys', [])
    item = get_object_or_404_json(models.Item, public_id=data['id'])
    if item.access(request.user):
        info = item.get_json(data['keys'])
        if not data['keys'] or 'stream' in data['keys']:
            info['stream'] = item.get_stream()
        if data['keys'] and 'layers' in data['keys']:
            info['layers'] = item.get_layers(request.user)
        if data['keys'] and 'documents' in data['keys']:
            info['documents'] = item.get_documents(request.user)
        if data['keys'] and 'files' in data['keys']:
            info['files'] = item.get_files(request.user)
        if not data['keys'] or 'groups' in data['keys'] \
                and item.editable(request.user):
            info['groups'] = [g.name for g in item.groups.all()]
        for k in settings.CONFIG['itemKeys']:
            if 'capability' in k \
                and not (item.editable(request.user) or has_capability(request.user, k['capability'])) \
                and k['id'] in info \
                and k['id'] not in ('parts', 'durations', 'duration'):
                    del info[k['id']]
        info['editable'] = item.editable(request.user)
        response['data'] = info
    else:
        #response = json_response(status=403, text='permission denied')
        response = json_response(status=404, text='not found')
    return render_to_json_response(response)
actions.register(get)

@login_required_json
def add(request, data):
    '''
    Adds a new item (without video)
    takes {
        title: string, // title (optional)
    }
    returns {
        id: string, // item id
        title: string, // title
        ... // more item properties
    }
    notes: To allow for this, set config option `itemRequiresVideo` to false.
    see: edit, find, get, lookup, remove, upload
    '''
    if not request.user.get_profile().capability('canAddItems'):
        response = json_response(status=403, text='permissino denied')
    else:
        data['title'] = data.get('title', 'Untitled')
        i = models.Item()
        i.data['title'] = data['title']
        i.user = request.user
        p = i.save()
        if p:
            p.wait()
        else:
            i.make_poster(True)
        response = json_response(status=200, text='created')
        response['data'] = i.get_json()
        add_changelog(request, data)
    return render_to_json_response(response)
actions.register(add, cache=False)

@login_required_json
def edit(request, data):
    '''
    Edits metadata of an item
    takes {
        id: string, // item id
        key: value, // item key and new value
        ... // more key/value pairs
    }
    returns {
        key: value // item key and new value
        ... // more key/value pairs
    }
    see: add, find, get, lookup, remove, upload
    '''
    update_clips = False
    item = get_object_or_404_json(models.Item, public_id=data['id'])
    if item.editable(request.user):
        response = json_response(status=200, text='ok')
        if 'rightslevel' in data:
            if request.user.get_profile().capability('canEditRightsLevel') == True:
                item.level = int(data['rightslevel'])
            else:
                response = json_response(status=403, text='permission denied')
            del data['rightslevel']
        if 'user' in data:
            if request.user.get_profile().get_level() in ('admin', 'staff') and \
                models.User.objects.filter(username=data['user']).exists():
                new_user = models.User.objects.get(username=data['user'])
                if new_user != item.user:
                    item.user = new_user
                    update_clips = True
            del data['user']
        if 'groups' in data:
            if not request.user.get_profile().capability('canManageUsers'):
                # Users wihtout canManageUsers can only add/remove groups they are not in
                groups = set([g.name for g in item.groups.all()])
                user_groups = set([g.name for g in request.user.groups.all()])
                other_groups = list(groups - user_groups)
                data['groups'] = [g for g in data['groups'] if g in user_groups] + other_groups
        add_changelog(request, data)
        r = item.edit(data)
        if r:
            r.wait()
        if update_clips:
            tasks.update_clips.delay(item.public_id)
        response['data'] = item.get_json()
    else:
        response = json_response(status=403, text='permission denied')
    return render_to_json_response(response)
actions.register(edit, cache=False)

@login_required_json
def remove(request, data):
    '''
    Removes an item
    takes {
        id: string // item id
    }
    returns {}
    notes: The return status code is 200 for success or 403 for permission denied.
    see: add, edit, find, get, lookup, upload
    '''
    response = json_response({})
    item = get_object_or_404_json(models.Item, public_id=data['id'])
    user = request.user
    if user.get_profile().capability('canRemoveItems') == True or \
           user.is_staff or \
           item.user == user or \
           item.groups.filter(id__in=user.groups.all()).count() > 0:
        add_changelog(request, data)
        #FIXME: is this cascading enough or do we end up with orphan files etc.
        item.delete()
        response = json_response(status=200, text='removed')
    else:
        response = json_response(status=403, text='permission denied')
    return render_to_json_response(response)
actions.register(remove, cache=False)

def setPosterFrame(request, data):
    '''
    Sets the poster frame for an item
    takes {
        id: string, // item id
        position: float // position in seconds
    }
    returns {}
    see: setPoster
    '''
    item = get_object_or_404_json(models.Item, public_id=data['id'])
    if item.editable(request.user):
        item.poster_frame = data['position']
        item.save()
        tasks.update_poster(item.public_id)
        response = json_response()
        add_changelog(request, data)
    else:
        response = json_response(status=403, text='permissino denied')
    return render_to_json_response(response)
actions.register(setPosterFrame, cache=False)


def setPoster(request, data):
    '''
    Sets the poster for an item
    takes {
        id: string, // item id
        source: string // poster url
    }
    returns {
        poster: {
            height: int, // height in px
            url: string, // poster url
            width: int // width in px
        }
    }
    see: setPosterFrame
    '''
    item = get_object_or_404_json(models.Item, public_id=data['id'])
    response = json_response()
    if item.editable(request.user):
        valid_sources = [p['source'] for p in item.get_posters()]
        if data['source'] in valid_sources:
            item.poster_source = data['source']
            if item.poster:
                item.poster.delete()
            item.save()
            tasks.update_poster(item.public_id)
            response = json_response()
            response['data']['posterAspect'] = item.poster_width/item.poster_height
            add_changelog(request, data)
        else:
            response = json_response(status=403, text='invalid poster url')
    else:
        response = json_response(status=403, text='permission denied')
    return render_to_json_response(response)
actions.register(setPoster, cache=False)

def updateExternalData(request, data):
    '''
    Updates metadata from an external service
    takes {
        id: string // item id
    }
    returns {}
    notes: This can be used to populate metadata from a remote source, like
    IMDb.
    see: getIds, getMetadata
    '''
    item = get_object_or_404_json(models.Item, public_id=data['id'])
    response = json_response()
    if item.editable(request.user):
        item.update_external()
    else:
        response = json_response(status=403, text='permission denied')
    return render_to_json_response(response)
actions.register(updateExternalData, cache=False)

def lookup(request, data):
    '''
    Looks up an item given partial metadata
    takes {
        director: [string], // directors (optional)
        id: string, // item id (optional)
        title: string, // title (optional)
        year: string // year (optional)
    }
    returns {
        director: [string], // director
        id: string, // item id
        title: string, // title
        year: string // year
    }
    see: add, edit, find, get, remove, upload
    '''
    if 'id' in data:
        i = models.Item.objects.get(public_id=data['id'])
        r = {'id': i.public_id}
        for key in ('title', 'director', 'year'):
            r[key] = i.get(key)
        response = json_response(r)
    else:
        response = json_response(status=404, text='not found')
    return render_to_json_response(response)
actions.register(lookup)


def frame(request, id, size, position=None):
    item = get_object_or_404(models.Item, public_id=id)
    if not item.access(request.user):
        return HttpResponseForbidden()
    frame = None
    if not position:
        if settings.CONFIG['media']['importFrames'] or item.poster_frame == -1:
            frames = item.poster_frames()
            if frames:
                position = item.poster_frame
                if position == -1 or position > len(frames):
                    position = int(len(frames)/2)
                position = frames[int(position)]['position']
            elif item.poster_frame == -1 and item.sort.duration:
                position = item.sort.duration/2
        else:
            position = item.poster_frame
    else:
        position = float(position.replace(',', '.'))

    if not frame:
        frame = item.frame(position, int(size))

    if not frame:
        frame = os.path.join(settings.STATIC_ROOT, 'jpg/list256.jpg')
        #raise Http404
    response = HttpFileResponse(frame, content_type='image/jpeg')
    if request.method == 'OPTIONS':
        response.allow_access()
    return response

def poster_frame(request, id, position):
    item = get_object_or_404(models.Item, public_id=id)
    if not item.access(request.user):
        return HttpResponseForbidden()
    position = int(position)
    frames = item.poster_frames()
    if frames and len(frames) > position:
        frame = frames[position]['path']
        return HttpFileResponse(frame, content_type='image/jpeg')
    raise Http404


def image_to_response(image, size=None):
    if size:
        size = int(size)
        path = image.path.replace('.jpg', '.%d.jpg'%size)
        if not os.path.exists(path):
            image_size = max(image.width, image.height)
            if size > image_size:
                path = image.path
            else:
                extract.resize_image(image.path, path, size=size)
    else:
        path = image.path
    return HttpFileResponse(path, content_type='image/jpeg')

def siteposter(request, id, size=None):
    item = get_object_or_404(models.Item, public_id=id)
    if not item.access(request.user):
        return HttpResponseForbidden()
    poster = item.path('siteposter.jpg')
    poster = os.path.abspath(os.path.join(settings.MEDIA_ROOT, poster))
    if size:
        size = int(size)
        image = Image.open(poster)
        image_size = max(image.size)
        if size < image_size:
            path = poster.replace('.jpg', '.%d.jpg'%size)
            extract.resize_image(poster, path, size=size)
            poster = path
    return HttpFileResponse(poster, content_type='image/jpeg')

def poster(request, id, size=None):
    item = get_object_or_404(models.Item, public_id=id)
    if not item.access(request.user):
        return HttpResponseForbidden()
    if not item.poster:
        poster_path = os.path.join(settings.MEDIA_ROOT, item.path('poster.jpg'))
        if os.path.exists(poster_path):
            item.poster.name = item.path('poster.jpg')
            item.poster_height = item.poster.height
            item.poster_width = item.poster.width
            models.Item.objects.filter(pk=item.id).update(
                poster=item.poster.name,
                poster_height=item.poster_height,
                poster_width=item.poster_width,
                icon=item.icon.name,
                json=item.get_json()
            )
    if item.poster:
        return image_to_response(item.poster, size)
    else:
        poster_path = os.path.join(settings.STATIC_ROOT, 'jpg/poster.jpg')
        response = HttpFileResponse(poster_path, content_type='image/jpeg')
        response['Cache-Control'] = 'no-cache'
        return response

def icon(request, id, size=None):
    item = get_object_or_404(models.Item, public_id=id)
    if not item.access(request.user):
        return HttpResponseForbidden()
    if item.icon:
        return image_to_response(item.icon, size)
    else:
        poster_path = os.path.join(settings.STATIC_ROOT, 'jpg/poster.jpg')
        response = HttpFileResponse(poster_path, content_type='image/jpeg')
        response['Cache-Control'] = 'no-cache'
        return response

def timeline(request, id, size, position=-1, format='jpg', mode=None):
    item = get_object_or_404(models.Item, public_id=id)
    if not item.access(request.user):
        return HttpResponseForbidden()

    if not mode:
        mode = 'antialias'
    modes = [t['id'] for t in settings.CONFIG['timelines']]
    if mode not in modes:
        raise Http404
    modes.pop(modes.index(mode))

    prefix = os.path.join(item.timeline_prefix, 'timeline')
    def timeline():
        timeline = '%s%s%sp' % (prefix, mode, size) 
        if position > -1:
            timeline += '%d' % int(position)
        return timeline + '.jpg'

    path = timeline()
    while modes and not os.path.exists(path):
        mode = modes.pop(0)
        path = timeline()
    response = HttpFileResponse(path, content_type='image/jpeg')
    if request.method == 'OPTIONS':
        response.allow_access()
    return response

def download(request, id, resolution=None, format='webm'):
    print 'download', id, resolution, format
    item = get_object_or_404(models.Item, public_id=id)
    if not resolution or int(resolution) not in settings.CONFIG['video']['resolutions']:
        resolution = max(settings.CONFIG['video']['resolutions'])
    else:
        resolution = int(resolution)
    if not item.access(request.user) or not item.rendered:
        return HttpResponseForbidden()
    ext = '.%s' % format
    parts = ['%s - %s ' % (item.get('title'), settings.SITENAME), item.public_id]
    if resolution != max(settings.CONFIG['video']['resolutions']):
        parts.append('.%dp' % resolution)
    parts.append(ext)
    filename = ''.join(parts)
    video = NamedTemporaryFile(suffix=ext)
    content_type = mimetypes.guess_type(video.name)[0]
    r = item.merge_streams(video.name, resolution, format)
    if not r:
        return HttpResponseForbidden()
    elif r == True:
        response = HttpResponse(FileWrapper(video), content_type=content_type)
        response['Content-Length'] = os.path.getsize(video.name)
    else:
        response = HttpFileResponse(r, content_type=content_type)
    response['Content-Disposition'] = "attachment; filename*=UTF-8''%s" % quote(filename.encode('utf-8'))
    return response

def torrent(request, id, filename=None):
    item = get_object_or_404(models.Item, public_id=id)
    if not item.access(request.user):
        return HttpResponseForbidden()
    if not item.torrent:
        raise Http404
    if not filename or filename.endswith('.torrent'):
        response = HttpResponse(item.get_torrent(request),
                                content_type='application/x-bittorrent')
        filename = utils.safe_filename("%s.torrent" % item.get('title'))
        response['Content-Disposition'] = "attachment; filename*=UTF-8''%s" % quote(filename.encode('utf-8'))
        return response
    while filename.startswith('/'):
        filename = filename[1:]
    filename = filename.replace('/../', '/')
    filename = item.path('torrent/%s' % filename)
    filename = os.path.abspath(os.path.join(settings.MEDIA_ROOT, filename))
    response = HttpFileResponse(filename)
    response['Content-Disposition'] = "attachment; filename*=UTF-8''%s" % \
                                      quote(os.path.basename(filename.encode('utf-8')))
    return response

def video(request, id, resolution, format, index=None, track=None):
    resolution = int(resolution)
    resolutions = sorted(settings.CONFIG['video']['resolutions'])
    if resolution not in resolutions:
        raise Http404
    item = get_object_or_404(models.Item, public_id=id)
    if not item.access(request.user):
        return HttpResponseForbidden()
    if index:
        index = int(index) - 1
    else:
        index = 0
    streams = item.streams(track)
    if index + 1 > streams.count():
        raise Http404
    stream = streams[index].get(resolution, format)
    if not stream.available or not stream.media:
        raise Http404
    path = stream.media.path

    #server side cutting
    #FIXME: this needs to join segments if needed
    t = request.GET.get('t')
    if t:
        def parse_timestamp(s):
            if ':' in s:
                s = ox.time2ms(s) / 1000
            return float(s)
        t = map(parse_timestamp, t.split(','))
        ext = '.%s' % format
        content_type = mimetypes.guess_type(path)[0]
        if len(t) == 2 and t[1] > t[0] and stream.info['duration']>=t[1]:
            response = HttpResponse(extract.chop(path, t[0], t[1]), content_type=content_type)
            filename = u"Clip of %s - %s-%s - %s %s%s" % (
                item.get('title'),
                ox.format_duration(t[0] * 1000).replace(':', '.')[:-4],
                ox.format_duration(t[1] * 1000).replace(':', '.')[:-4],
                settings.SITENAME,
                item.public_id,
                ext
            )
            response['Content-Disposition'] = "attachment; filename*=UTF-8''%s" % quote(filename.encode('utf-8'))
            return response
        else:
            filename = "%s - %s %s%s" % (
                item.get('title'),
                settings.SITENAME,
                item.public_id,
                ext
            )
            response = HttpFileResponse(path, content_type=content_type)
            response['Content-Disposition'] = "attachment; filename*=UTF-8''%s" % quote(filename.encode('utf-8'))
            return response
    if not settings.XSENDFILE and not settings.XACCELREDIRECT:
        return redirect(stream.media.url)
    response = HttpFileResponse(path)
    response['Cache-Control'] = 'public'
    return response

def srt(request, id, layer, language=None, index=None):
    item = get_object_or_404(models.Item, public_id=id)
    if not item.access(request.user):
        response = HttpResponseForbidden()
    else:
        response = HttpResponse()
        if language:
            filename = u"%s.%s.srt" % (item.get('title'), language)
        else:
            filename = u"%s.srt" % item.get('title')
        response['Content-Disposition'] = "attachment; filename*=UTF-8''%s" % quote(filename.encode('utf-8'))
        response['Content-Type'] = 'text/x-srt'
        response.write(item.srt(layer, language))
    return response

def random_annotation(request):
    n = models.Item.objects.all().count()
    pos = random.randint(0, n)
    item = models.Item.objects.all()[pos]
    n = item.annotations.all().count()
    pos = random.randint(0, n)
    clip = item.annotations.all()[pos]
    return redirect('/%s'% clip.public_id)

def atom_xml(request):
    add_updated = True
    feed = ET.Element("feed")
    feed.attrib['xmlns'] = 'http://www.w3.org/2005/Atom'
    feed.attrib['xmlns:media'] = 'http://search.yahoo.com/mrss/'
    feed.attrib['xml:lang'] = 'en'
    title = ET.SubElement(feed, "title")
    title.text = settings.SITENAME
    title.attrib['type'] = 'text'
    link = ET.SubElement(feed, "link")
    link.attrib['rel'] = 'self'
    link.attrib['type'] = 'application/atom+xml'
    atom_link = request.build_absolute_uri('/atom.xml')
    link.attrib['href'] = atom_link
    '''
    rights = ET.SubElement(feed, 'rights')
    rights.attrib['type'] = 'text'
    rights.text = "PGL"
    '''
    el = ET.SubElement(feed, 'id')
    el.text = atom_link

    level = settings.CONFIG['capabilities']['canSeeItem']['guest']
    if not request.user.is_anonymous():
        level = request.user.get_profile().level
    for item in models.Item.objects.filter(level__lte=level, rendered=True).order_by('-created')[:7]:
        if add_updated:
            updated = ET.SubElement(feed, "updated")
            updated.text = item.modified.strftime("%Y-%m-%dT%H:%M:%SZ")
            add_updated = False

        page_link = request.build_absolute_uri('/%s' % item.public_id)

        entry = ET.Element("entry")
        title = ET.SubElement(entry, "title")
        title.text = ox.decode_html(item.get('title'))
        link = ET.SubElement(entry, "link")
        link.attrib['rel'] = 'alternate'
        link.attrib['href'] = "%s/info" % page_link
        updated = ET.SubElement(entry, "updated")
        updated.text = item.modified.strftime("%Y-%m-%dT%H:%M:%SZ")
        published = ET.SubElement(entry, "published")
        published.text = item.created.strftime("%Y-%m-%dT%H:%M:%SZ")
        el = ET.SubElement(entry, "id")
        el.text = page_link

        if item.get('director'):
            el = ET.SubElement(entry, "author")
            name = ET.SubElement(el, "name")
            name.text = ox.decode_html(u', '.join(item.get('director')))
        elif item.user:
            el = ET.SubElement(entry, "author")
            name = ET.SubElement(el, "name")
            name.text = item.user.username

        for topic in item.get('topics', []):
          el = ET.SubElement(entry, "category")
          el.attrib['term'] = topic

        '''
        el = ET.SubElement(entry, "rights")
        el.text = "PGL"
        el = ET.SubElement(entry, "link")
        el.attrib['rel'] = "license"
        el.attrib['type'] = "text/html"
        el.attrib['href'] = item.licenseUrl
        '''
        '''
        el = ET.SubElement(entry, "contributor")
        name = ET.SubElement(el, "name")
        name.text = item.user.username
        '''

        description = item.get('description', item.get('summary'))
        if description:
            content = ET.SubElement(entry, "content")
            content.attrib['type'] = 'html'
            content.text = description

        format = ET.SubElement(entry, "format")
        format.attrib['xmlns'] = 'http://transmission.cc/FileFormat'
        streams = item.streams().filter(source=None).order_by('-id')
        if streams.exists():
            stream = streams[0]
            for key in ('size', 'duration', 'video_codec',
                        'framerate', 'width', 'height',
                        'audio_codec', 'samplerate', 'channels'):
                value = stream.info.get(key)
                if not value and stream.info.get('video'):
                    value = stream.info['video'][0].get({
                        'video_codec': 'codec'
                    }.get(key, key))
                if not value and stream.info.get('audio'):
                    value = stream.info['audio'][0].get({
                        'audio_codec': 'codec'
                    }.get(key, key))
                if value and value !=  -1:
                    el = ET.SubElement(format, key)
                    el.text = unicode(value)
        el = ET.SubElement(format, 'pixel_aspect_ratio')
        el.text = u"1:1"

        if has_capability(request.user, 'canDownloadVideo'):
            if item.torrent:
                el = ET.SubElement(entry, "link")
                el.attrib['rel'] = 'enclosure'
                el.attrib['type'] = 'application/x-bittorrent'
                el.attrib['href'] = '%s/torrent/' % page_link
                el.attrib['length'] = '%s' % ox.get_torrent_size(item.torrent.path)
            #FIXME: loop over streams
            #for s in item.streams().filter(resolution=max(settings.CONFIG['video']['resolutions'])):
            for s in item.streams().filter(source=None):
                el = ET.SubElement(entry, "link")
                el.attrib['rel'] = 'enclosure'
                el.attrib['type'] = 'video/%s' % s.format
                el.attrib['href'] = '%s/%sp.%s' % (page_link, s.resolution, s.format)
                el.attrib['length'] = '%s'%s.media.size

        el = ET.SubElement(entry, "media:thumbnail")
        thumbheight = 96
        thumbwidth = int(thumbheight * item.stream_aspect)
        thumbwidth -= thumbwidth % 2
        el.attrib['url'] = '%s/%sp.jpg' % (page_link, thumbheight)
        el.attrib['width'] = str(thumbwidth)
        el.attrib['height'] = str(thumbheight)
        feed.append(entry)     
    return HttpResponse(
        '<?xml version="1.0" encoding="utf-8" ?>\n' + ET.tostring(feed),
        'application/atom+xml'
    )

def oembed(request):
    format = request.GET.get('format', 'json')
    maxwidth = int(request.GET.get('maxwidth', 640))
    maxheight = int(request.GET.get('maxheight', 480))

    url = request.GET['url']
    parts = urlparse(url).path.split('/')
    public_id = parts[1]
    item = get_object_or_404_json(models.Item, public_id=public_id)
    embed_url = request.build_absolute_uri('/%s' % public_id)
    if url.startswith(embed_url):
        embed_url = url
    if not '#embed' in embed_url:
        embed_url = '%s#embed' % embed_url

    oembed = {}
    oembed['version'] = '1.0'
    oembed['type'] = 'video'
    oembed['provider_name'] = settings.SITENAME
    oembed['provider_url'] = request.build_absolute_uri('/')
    oembed['title'] = item.get('title')
    #oembed['author_name'] = item.get('director')
    #oembed['author_url'] = ??
    height = max(settings.CONFIG['video']['resolutions'])
    height = min(height, maxheight)
    width = int(round(height * item.stream_aspect))
    if width > maxwidth:
        width = maxwidth
        height = min(maxheight, int(width / item.stream_aspect))
    oembed['html'] = '<iframe width="%s" height="%s" src="%s" frameborder="0" allowfullscreen></iframe>' % (width, height, embed_url)
    oembed['width'] = width
    oembed['height'] = height
    thumbheight = 96
    thumbwidth = int(thumbheight * item.stream_aspect)
    thumbwidth -= thumbwidth % 2
    oembed['thumbnail_height'] = thumbheight
    oembed['thumbnail_width'] = thumbwidth
    oembed['thumbnail_url'] = request.build_absolute_uri('/%s/%sp.jpg' % (item.public_id, thumbheight))
    if format == 'xml':
        oxml = ET.Element('oembed')
        for key in oembed:
            e = ET.SubElement(oxml, key)
            e.text = unicode(oembed[key])
        return HttpResponse(
            '<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n' + ET.tostring(oxml),
            'application/xml'
        )
    return HttpResponse(json.dumps(oembed, indent=2), 'application/json')

def sitemap_xml(request):
    sitemap = os.path.abspath(os.path.join(settings.MEDIA_ROOT, 'sitemap.xml'))
    if not os.path.exists(sitemap):
        tasks.update_sitemap(request.build_absolute_uri('/'))
    elif time.mktime(time.localtime()) - os.stat(sitemap).st_ctime > 24*60*60:
        tasks.update_sitemap.delay(request.build_absolute_uri('/'))
    response = HttpFileResponse(sitemap)
    response['Content-Type'] = 'application/xml'
    return response

def item_json(request, id):
    level = settings.CONFIG['capabilities']['canSeeItem']['guest']
    if not request.user.is_anonymous():
        level = request.user.get_profile().level
    qs = models.Item.objects.filter(public_id=id, level__lte=level)
    if qs.count() == 0:
        response = json_response(status=404, text='not found')
    else:
        item = qs[0]
        response = item.get_json()
        response['layers'] = item.get_layers(request.user)
    return render_to_json_response(response)

def item_xml(request, id):
    level = settings.CONFIG['capabilities']['canSeeItem']['guest']
    if not request.user.is_anonymous():
        level = request.user.get_profile().level
    qs = models.Item.objects.filter(public_id=id, level__lte=level)
    if qs.count() == 0:
        response = json_response(status=404, text='not found')
        response = render_to_json_response(response)
    else:
        item = qs[0]
        j = item.get_json()
        j['layers'] = item.get_layers(request.user)
        if 'resolution' in j:
            j['resolution'] = {'width': j['resolution'][0], 'height':j['resolution'][1]}
        def xmltree(root, key, data):
            if isinstance(data, list) or \
                isinstance(data, tuple):
                e = ET.SubElement(root, key)
                for value in data:
                    xmltree(e, key, value)
            elif isinstance(data, dict):
                for k in data:
                    if data[k]:
                        xmltree(root, k, data[k])
            else:
                e = ET.SubElement(root, key)
                e.text = unicode(data)

        oxml = ET.Element('item')
        xmltree(oxml, 'item', j)
        response = HttpResponse(
            '<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n' + ET.tostring(oxml),
            'application/xml'
        )
    return response

def item(request, id):
    id = id.split('/')[0]
    view = None
    template = 'index.html'
    level = settings.CONFIG['capabilities']['canSeeItem']['guest']
    if not request.user.is_anonymous():
        level = request.user.get_profile().level
    qs = models.Item.objects.filter(public_id=id, level__lte=level)
    if qs.count() == 0:
        context = RequestContext(request, {
            'base_url': request.build_absolute_uri('/'),
            'settings': settings
        })
    else:
        item = qs[0]
        template = 'item.html'
        keys = [
            'year',
            'director',
            'writer',
            'producer',
            'cinematographer',
            'editor',
            'actor',
            'topic',
        ]
        if not settings.USE_IMDB:
            keys += [
                'summary'
            ]
        keys += [
            'duration'
            'aspectratio'
            'hue',
            'saturation',
            'lightness',
            'volume',
            'numberofcuts',
        ]

        data = []
        for k in keys:
            value = item.get(k)
            key = utils.get_by_id(settings.CONFIG['itemKeys'], k)
            if value:
                if k == 'actor':
                    title = 'Cast'
                else:
                    title = key['title'] if key else k.capitalize()
                if isinstance(value, list):
                    value = value = u', '.join([unicode(v) for v in value])
                elif key and key.get('type') == 'float':
                    value = '%0.3f' % value
                elif key  and key.get('type') == 'time':
                    value = ox.format_duration(value * 1000)
                data.append({'key': k, 'title': title, 'value': value})
        clips = []
        clip = {'in': 0, 'annotations': []}
        #logged in users should have javascript. not adding annotations makes load faster
        if not settings.USE_IMDB and request.user.is_anonymous():
            for a in item.annotations.exclude(
                layer='subtitles'
            ).exclude(
                value=''
            ).filter(
                layer__in=models.Annotation.public_layers()
            ).order_by('start', 'end', 'sortvalue'):
                if clip['in'] < a.start:
                    if clip['annotations']:
                        clip['annotations'] = '<br />\n'.join(clip['annotations'])
                        clips.append(clip)
                    clip = {'in': a.start, 'annotations': []}
                clip['annotations'].append(a.value)
            if clip['annotations']:
                clip['annotations'] = '<br />\n'.join(clip['annotations'])
                clips.append(clip)
        head_title = item.get('title', '')
        title = item.get('title', '')
        if item.get('director'):
            head_title += u' (%s)' % u', '.join(item.get('director', []))
        if item.get('year'):
            head_title += u' %s' % item.get('year')
            title += u' (%s)' % item.get('year')
        if view:
            head_title += u' – %s' % view
        head_title += u' – %s' % settings.SITENAME
        head_title = ox.decode_html(head_title)
        title = ox.decode_html(title)
        ctx = {
            'current_url': request.build_absolute_uri(request.get_full_path()),
            'base_url': request.build_absolute_uri('/'),
            'url': request.build_absolute_uri('/%s' % id),
            'id': id,
            'settings': settings,
            'data': data,
            'clips': clips,
            'icon': settings.CONFIG['user']['ui']['icons'] == 'frames' and 'icon' or 'poster',
            'title': title,
            'head_title': head_title,
            'description': item.get_item_description(),
            'description_html': item.get_item_description_html()
        }
        if not settings.USE_IMDB:
            value = item.get('topic' in keys and 'topic' or 'keywords')
            if isinstance(value, list):
                value = value = ', '.join(value)
            if value:
                ctx['keywords'] = ox.strip_tags(value)

        context = RequestContext(request, ctx)
    return render_to_response(template, context)

