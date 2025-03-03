# -*- coding: utf-8 -*-

from ox.utils import json
from oxdjango.shortcuts import render_to_json_response, json_response

from itemlist.views import get_list_or_404_json
from oxdjango.api import actions

from . import models

def tv(request, data):
    '''
    Gets the current TV program for a given list
    takes {
        list: string // list name
    }
    returns {
        item: string, // current item
        position: float, // current position in seconds
        title: string, // item title
        ... // more item properties
    }
    '''
    if 'list' in data and data['list']:
        list = get_list_or_404_json(data['list'])
        if list.accessible(request.user):
            channel, created = models.Channel.objects.get_or_create(list=list)
            response = json_response(status=200, text='created')
            response['data'] = channel.json(request.user)
        else:
            response = json_response(status=404, text='list not found')
    else:
        channel, created = models.Channel.objects.get_or_create(list=None)
        response = json_response(status=200, text='ok')
        response['data'] = channel.json(request.user)
    return render_to_json_response(response)
actions.register(tv, cache=False)
