# -*- coding: utf-8 -*-

import os
import re

from django.db.models import Max, Sum
from django.db import transaction
from django.conf import settings
from ox.utils import json
from oxdjango.decorators import login_required_json
from oxdjango.shortcuts import render_to_json_response, get_object_or_404_json, json_response
from oxdjango.http import HttpFileResponse


from . import models
from oxdjango.api import actions
from item import utils
from item.models import Item
from user.tasks import update_numberoflists
from changelog.models import add_changelog

def get_list_or_404_json(id):
    id = id.split(':')
    username = id[0]
    listname = ":".join(id[1:])
    return get_object_or_404_json(models.List, user__username=username, name=listname)

def _order_query(qs, sort):
    order_by = []
    for e in sort:
        operator = e['operator']
        if operator != '-':
            operator = ''
        key = {
            'subscribed': 'subscribed_users',
            'items': 'numberofitems'
        }.get(e['key'], e['key'])
        order = '%s%s' % (operator, key)
        order_by.append(order)
        if key == 'subscribers':
            qs = qs.annotate(subscribers=Sum('subscribed_users'))
    if order_by:
        qs = qs.order_by(*order_by, nulls_last=True)
    qs = qs.distinct()
    return qs

def parse_query(data, user):
    query = {}
    query['range'] = [0, 100]
    query['sort'] = [{'key':'user', 'operator':'+'}, {'key':'name', 'operator':'+'}]
    for key in ('keys', 'group', 'list', 'range', 'position', 'positions', 'sort'):
        if key in data:
            query[key] = data[key]
    query['qs'] = models.List.objects.find(data, user)
    return query


def findLists(request, data):
    '''
    Finds lists for a given query
    takes {
        query: object, // query object, see `find`
        sort: [], // list of sort objects, see `find`
        range: [int, int], // range of results to return
        keys: [string] // list of properties to return
    }
    returns {
        items: [object] // list of list objects
    }
    notes: Possible query keys are 'featured', 'name', 'subscribed' and 'user',
    possible keys are 'featured', 'name', 'query', 'subscribed' and 'user'.
    see: addList, editList, find, getList, removeList, sortLists
    '''
    query = parse_query(data, request.user)

    #order
    is_section_request = query['sort'] == [{'operator': '+', 'key': 'position'}]
    def is_featured_condition(x):
        return x['key'] == 'status' and \
               x['value'] == 'featured' and \
               x['operator'] in ('=', '==')
    is_featured = any(
        is_featured_condition(x)
        for x in data.get('query', {}).get('conditions', [])
    )

    is_personal = request.user.is_authenticated and any(
        (x['key'] == 'user' and x['value'] == request.user.username and x['operator'] == '==')
        for x in data.get('query', {}).get('conditions', [])
    )

    if is_section_request:
        qs = query['qs']
        if not is_featured and not request.user.is_anonymous:
            qs = qs.filter(position__in=models.Position.objects.filter(user=request.user))
        qs = qs.order_by('position__position')
    else:
        qs = _order_query(query['qs'], query['sort'])

    if is_personal and request.user.profile.ui.get('hidden', {}).get('lists'):
        qs = qs.exclude(name__in=request.user.profile.ui['hidden']['lists'])

    response = json_response()
    if 'keys' in data:
        qs = qs[query['range'][0]:query['range'][1]]

        response['data']['items'] = [l.json(data['keys'], request.user) for l in qs]
    elif 'position' in data:
        #FIXME: actually implement position requests
        response['data']['position'] = 0
    elif 'positions' in data:
        ids = [i.get_id() for i in qs]
        response['data']['positions'] = utils.get_positions(ids, query['positions'])
    else:
        response['data']['items'] = qs.count()
    return render_to_json_response(response)
actions.register(findLists)

def getList(request, data):
    '''
    Gets a list by id
    takes {
        id: string // list id
    }
    returns {
        id: string, // list id
        section: string, // lists section (like 'personal')
        ... // more key/value pairs
    }
    see: addList, editList, findLists, removeList, sortLists
    '''
    if 'id' in data:
        response = json_response()
        list = get_list_or_404_json(data['id'])
        if list.accessible(request.user):
            response['data'] = list.json(user=request.user)
        else:
            response = json_response(status=403, text='not allowed')
    else:
        response = json_response(status=404, text='not found')
    return render_to_json_response(response)
actions.register(getList)

@login_required_json
def addListItems(request, data):
    '''
    Adds one or more items to a static list
    takes {
        list: string, // list id
        items: [string], // either list of item ids
        query: object // or query object, see `find`
    }
    returns {}
    see: find, orderListItems, removeListItems
    '''
    list = get_list_or_404_json(data['list'])
    if 'items' in data:
        if list.editable(request.user):
            with transaction.atomic():
                for item in Item.objects.filter(public_id__in=data['items']):
                    list.add(item)
            response = json_response(status=200, text='items added')
            add_changelog(request, data, data['list'])
        else:
            response = json_response(status=403, text='not allowed')
    elif 'query' in data:
        response = json_response(status=501, text='not implemented')
    else:
        response = json_response(status=501, text='not implemented')
    return render_to_json_response(response)
actions.register(addListItems, cache=False)


@login_required_json
def removeListItems(request, data):
    '''
    Removes one or more items from a static list
    takes {
         list: string, // list id
         items: [itemId], // either list of item ids
         query: object // or query object, see `find`
    }
    returns {}
    see: addListItems, find, orderListItems
    '''
    list = get_list_or_404_json(data['list'])
    if 'items' in data:
        if list.editable(request.user):
            list.remove(items=data['items'])
            response = json_response(status=200, text='items removed')
            add_changelog(request, data, data['list'])
        else:
            response = json_response(status=403, text='not allowed')
    elif 'query' in data:
        response = json_response(status=501, text='not implemented')

    else:
        response = json_response(status=501, text='not implemented')
    return render_to_json_response(response)
actions.register(removeListItems, cache=False)

@login_required_json
def orderListItems(request, data):
    '''
    Sets the manual ordering of items in a given list
    takes {
       list: string, // list id
       ids: [string] // ordered list of item ids
    }
    returns {}
    notes: There is no UI for this yet.
    see: addListItems, removeListItems
    '''
    list = get_list_or_404_json(data['list'])
    response = json_response()
    if list.editable(request.user) and list.type == 'static':
        index = 0
        with transaction.atomic():
            for i in data['ids']:
                models.ListItem.objects.filter(list=list, item__public_id=i).update(index=index)
                index += 1
    else:
        response = json_response(status=403, text='permission denied')
    return render_to_json_response(response)
actions.register(orderListItems, cache=False)


@login_required_json
def addList(request, data):
    '''
    Adds a new list
    takes {
        name: value, // list name (optional)
        ... // more key/value pairs
    }
    returns {
        id: string, // list id
        name: string, // list name
        ... // more key/value pairs
    }
    notes: Possible keys are 'description', 'items', 'name', 'query', 'sort',
    'type' and 'view'.
    see: editList, findLists, getList, removeList, sortLists
    '''
    data['name'] = re.sub(r' \[\d+\]$', '', data.get('name', 'Untitled')).strip()
    name = data['name']
    if not name:
        name = "Untitled"
    num = 1
    created = False
    while not created:
        list, created = models.List.objects.get_or_create(name=name, user=request.user)
        num += 1
        name = data['name'] + ' [%d]' % num

    del data['name']
    if data:
        list.edit(data, request.user)
    else:
        list.save()
    update_numberoflists.delay(request.user.username)

    if 'items' in data:
        for item in Item.objects.filter(public_id__in=data['items']):
            list.add(item)

    if list.status == 'featured':
        pos, created = models.Position.objects.get_or_create(list=list,
                                         user=request.user, section='featured')
        qs = models.Position.objects.filter(section='featured')
    else:
        pos, created = models.Position.objects.get_or_create(list=list,
                                         user=request.user, section='personal')
        qs = models.Position.objects.filter(user=request.user, section='personal')
    pos.position = qs.aggregate(Max('position'))['position__max'] + 1
    pos.save()
    response = json_response(status=200, text='created')
    response['data'] = list.json(user=request.user)
    add_changelog(request, data, list.get_id())
    return render_to_json_response(response)
actions.register(addList, cache=False)


@login_required_json
def editList(request, data):
    '''
    Edits a list
    takes {
        id: string, // list id
        key: value, // property id and new value
        ... // more key/value pairs
    }
    returns {
        id: string, // list id
        ... // more key/value pairs
    }
    notes: Possible keys are 'name', 'position', 'posterFrames', 'query' and
    'status'. 'posterFrames' is an array of {item, position}. If you change
    'status', you have to pass 'position' (the position of the list in its new
    list folder).
    see: addList, findLists, getList, removeList, sortLists
    '''
    list = get_list_or_404_json(data['id'])
    if list.editable(request.user):
        response = json_response()
        list.edit(data, request.user)
        response['data'] = list.json(user=request.user)
        add_changelog(request, data)
    else:
        response = json_response(status=403, text='not allowed')
    return render_to_json_response(response)
actions.register(editList, cache=False)

@login_required_json
def removeList(request, data):
    '''
    Removes a list
    takes {
        id: string // list id
    }
    returns {}
    see: addList, editList, findLists, getList, sortLists
    '''
    list = get_list_or_404_json(data['id'])
    response = json_response()
    if list.editable(request.user):
        add_changelog(request, data)
        list.delete()
        update_numberoflists.delay(request.user.username)
    else:
        response = json_response(status=403, text='not allowed')
    return render_to_json_response(response)
actions.register(removeList, cache=False)


@login_required_json
def subscribeToList(request, data):
    '''
    Adds a list to favorites
    takes {
        id: string, // list id
        user: string // username (admin-only)
    }
    returns {}
    see: unsubscribeFromList
    '''
    list = get_list_or_404_json(data['id'])
    user = request.user
    if list.status == 'public' and \
       list.subscribed_users.filter(username=user.username).count() == 0:
        list.subscribed_users.add(user)
        pos, created = models.Position.objects.get_or_create(list=list, user=user, section='public')
        if created:
            qs = models.Position.objects.filter(user=user, section='public')
            pos.position = qs.aggregate(Max('position'))['position__max'] + 1
            pos.save()
        add_changelog(request, data)
    response = json_response()
    return render_to_json_response(response)
actions.register(subscribeToList, cache=False)


@login_required_json
def unsubscribeFromList(request, data):
    '''
    Removes a list from favorites
    takes {
        id: string, // list id
        user: string // username (admin-only)
    }
    returns {}
    see: subscribeToList
    '''
    list = get_list_or_404_json(data['id'])
    user = request.user
    list.subscribed_users.remove(user)
    models.Position.objects.filter(list=list, user=user, section='public').delete()
    response = json_response()
    add_changelog(request, data)
    return render_to_json_response(response)
actions.register(unsubscribeFromList, cache=False)


@login_required_json
def sortLists(request, data):
    '''
    Sets the order of lists in a given section
    takes {
        section: string, // lists section
        ids: [string] // ordered list of lists
    }
    returns {}
    notes: Possible sections are 'personal', 'favorite' and 'featured'. Setting
    the order of featured lists requires the appropriate capability.
    see: addList, editList, findLists, getList, removeList
    '''
    position = 0
    section = data['section']
    section = {
        'favorite': 'public'
    }.get(section,section)
    #ids = list(set(data['ids']))
    ids = data['ids']
    if section == 'featured' and not request.user.profile.capability('canEditFeaturedLists'):
        response = json_response(status=403, text='not allowed')
    else:
        user = request.user
        if section == 'featured':
            for i in ids:
                l = get_list_or_404_json(i)
                qs = models.Position.objects.filter(section=section, list=l)
                if qs.count() > 0:
                    pos = qs[0]
                else:
                    pos = models.Position(list=l, user=user, section=section)
                if pos.position != position:
                    pos.position = position
                    pos.save()
                position += 1
                models.Position.objects.filter(section=section, list=l).exclude(id=pos.id).delete()
        else:
            for i in ids:
                try:
                    l = get_list_or_404_json(i)
                except:
                    continue
                pos, created = models.Position.objects.get_or_create(list=l,
                                            user=request.user, section=section)
                if pos.position != position:
                    pos.position = position
                    pos.save()
                position += 1

        response = json_response()
    return render_to_json_response(response)
actions.register(sortLists, cache=False)


def icon(request, id, size=16):
    if not size:
        size = 16

    id = id.split(':')
    username = id[0]
    listname = ":".join(id[1:])
    qs = models.List.objects.filter(user__username=username, name=listname)
    if qs.count() == 1 and qs[0].accessible(request.user):
        list = qs[0]
        icon = list.get_icon(int(size))
    else:
        icon = os.path.join(settings.STATIC_ROOT, 'jpg/list256.jpg')
    return HttpFileResponse(icon, content_type='image/jpeg')
