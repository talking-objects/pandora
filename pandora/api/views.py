# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division, with_statement

import os
import copy

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.conf import settings
from django.db.models import Max, Sum

from ox.django.shortcuts import render_to_json_response, json_response
from ox.utils import json

from user.models import init_user

from actions import actions


def api(request):
    if request.META['REQUEST_METHOD'] == "OPTIONS":
        response = render_to_json_response({'status': {'code': 200,
                                                       'text': 'use POST'}})
        response['Access-Control-Allow-Origin'] = '*'
        return response
    if not 'action' in request.POST:
        methods = actions.keys()
        api = []
        for f in sorted(methods):
            api.append({'name': f,
                        'doc': actions.doc(f).replace('\n', '<br>\n')})
        context = RequestContext(request, {'api': api,
                                           'sitename': settings.SITENAME})
        return render_to_response('api.html', context)
    function = request.POST['action']
    #FIXME: possible to do this in f
    #data = json.loads(request.POST['data'])

    f = actions.get(function)
    if f:
        response = f(request)
    else:
        response = render_to_json_response(json_response(status=400,
                                text='Unknown function %s' % function))
    response['Access-Control-Allow-Origin'] = '*'
    return response


def init(request):
    '''
        return {'status': {'code': int, 'text': string},
                'data': {user: object}}
    '''
    response = json_response({})
    config = copy.deepcopy(settings.CONFIG)
    del config['keys'] #is this needed?

    response['data']['site'] = config
    response['data']['user'] = init_user(request.user, request)
    return render_to_json_response(response)
actions.register(init)


def error(request):
    '''
     this action is used to test api error codes, it should return a 503 error
    '''
    success = error_is_success
    return render_to_json_response({})
actions.register(error)
