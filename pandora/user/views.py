# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
import random
random.seed()
import re

from django.contrib.auth import authenticate, login, logout
from django.template import RequestContext, loader
from django.utils import simplejson as json
from django.conf import settings
from django.core.mail import send_mail, BadHeaderError, EmailMessage
from django.shortcuts import redirect
from django.db.models import Max
from django.contrib.auth.models import User, Group

from ox.django.shortcuts import render_to_json_response, json_response, get_object_or_404_json
from ox.django.decorators import login_required_json
import ox


from ox.django.api import actions
from item.models import Access, Item
from item import utils 
from changelog.models import add_changelog

import models
from decorators import capability_required_json
import persona


def get_user_or_404(data):
    if 'id' in data:
        u = get_object_or_404_json(User, id=ox.fromAZ(data['id']))
    else:
        u = get_object_or_404_json(User, username=data['username'])
    return u


def get_group_or_404(data):
    if 'id' in data:
        g = get_object_or_404_json(Group, id=ox.fromAZ(data['id']))
    else:
        g = get_object_or_404_json(Group, name=data['name'])
    return g


def signin(request, data):
    '''
    Sign in
    takes {
        username: string,
        password: string
    }
    returns {
        errors: {
            username: 'Unknown Username',
            password: 'Incorrect Password'
        }
        user: {
            ...
        }
    }
    see: signout, signup
    '''
    if 'assertion' in data:
        response = persona.signin(request)
    elif 'username' in data and 'password' in data:
        data['username'] = data['username'].strip()
        if settings.AUTH_CHECK_USERNAME:
            qs = User.objects.filter(username__iexact=data['username'])
            if qs.count() == 0:
                response = json_response({
                    'errors': {
                        'username': 'Unknown Username'
                    }
                })
                username = None
            else:
                username = qs[0].username
        else:
            username = data['username']
        if username:
            user = authenticate(username=username, password=data['password'])
            if user is not None:
                if user.is_active:
                    request.session['ui'] = '{}'
                    login(request, user)
                    user_json = models.init_user(user, request)
                    response = json_response({
                        'user': user_json
                    })
                else:
                    response = json_response({
                        'errors': {
                            'username': 'User Disabled'
                        }
                    })
            else:
                response = json_response({
                    'errors': {
                        'password': 'Incorrect Password'
                    }
                })
    else:
        response = json_response(status=400, text='invalid data')
    return render_to_json_response(response)
actions.register(signin, cache=False)


def signout(request, data):
    '''
    Sign out
    takes {}
    returns {
        user: { // default user
            key: value, // user data
            ... // more user daa
        }
    }
    see: signin, signup
    '''
    response = json_response(text='ok')
    if request.user.is_authenticated():
        profile = request.user.get_profile()
        if profile.ui.get('page') == 'signout':
            profile.ui['page'] = ''
            profile.save()
        response = json_response(text='logged out')
        logout(request)

    response['data']['user'] = settings.CONFIG['user']
    return render_to_json_response(response)
actions.register(signout, cache=False)


def signup(request, data):
    '''
    Sign up
    takes {
        username: string,
        password: string,
        email: string
    }

    returns {
        errors: {
            username: 'Unknown Username',
            password: 'Incorrect Password'
        }
        user: {
            ...
        }
    }
    see: signin, signout
    '''
    if 'username' in data and 'password' in data:
        data['username'] = data['username'].strip()
        if 'email' in data:
            data['email'] = ox.escape_html(data['email'])
        if User.objects.filter(username__iexact=data['username']).count() > 0:
            response = json_response({
                'errors': {
                    'username': 'Username already exists'
                }
            })
        elif User.objects.filter(email__iexact=data['email']).count() > 0:
            response = json_response({
                'errors': {
                    'email': 'Email address already exists'
                }
            })
        elif not data['password']:
            response = json_response({
                'errors': {
                    'password': 'Password can not be empty'
                }
            })
        else:
            first_user = User.objects.count() == 0
            user = User(username=data['username'], email=data['email'])
            user.set_password(data['password'])
            #make first user admin
            user.is_superuser = first_user
            user.is_staff = first_user
            user.save()
            #create default user lists:
            for l in settings.CONFIG['personalLists']:
                list = models.List(name=l['title'], user=user)
                for key in ('query', 'public', 'featured'):
                    if key in l:
                        setattr(list, key, l[key])
                        if key == 'query':
                            for c in list.query['conditions']:
                                if c['key'] == 'user':
                                    c['value'] = c['value'].format(username=user.username)
                list.save()
                pos = models.Position(list=list, section='personal', user=user)
                qs = models.Position.objects.filter(user=user, section='personal')
                pos.position = (qs.aggregate(Max('position'))['position__max'] or 0) + 1
                pos.save()
            if request.session.session_key:
                models.SessionData.objects.filter(session_key=request.session.session_key).update(user=user)
            ui = json.loads(request.session.get('ui', 'null'))
            user = authenticate(username=data['username'],
                                password=data['password'])
            if ui:
                profile = user.get_profile()
                profile.ui = ui
                profile.save()

            login(request, user)
            user_json = models.init_user(user, request)
            response = json_response({
                'user': user_json
            }, text='account created')
    else:
        response = json_response(status=400, text='invalid data')
    return render_to_json_response(response)
actions.register(signup, cache=False)


def resetPassword(request, data):
    '''
    Resets password for a given user
    takes {
        username: string, // username
        password: string, // password
        code: string // token
    }
    returns {
        errors: {
            code: 'Incorrect Code' // on error
        },
        user: object // on success
    }
    see: resetPassword
    '''
    if 'code' in data and 'password' in data:
        if not data['password']:
            response = json_response({
                'errors': {
                    'password': 'Password can not be empty'
                }
            })
        else:
            qs = models.UserProfile.objects.filter(reset_code=data['code'])
            if qs.count() == 1:
                user = qs[0].user
                user.set_password(data['password'])
                user.save()
                user_profile = user.get_profile()
                user_profile.reset_code = None
                user_profile.save()
                user = authenticate(username=user.username, password=data['password'])
                login(request, user)

                user_json = models.init_user(user, request)
                response = json_response({
                    'user': user_json
                }, text='password reset')
            else:
                response = json_response({
                    'errors': {
                        'code': 'Incorrect code'
                    }
                })

    else:
        response = json_response(status=400, text='invalid data')
    return render_to_json_response(response)
actions.register(resetPassword, cache=False)


def requestToken(request, data):
    '''
    Requests a password reset token
    takes {
        username: string, // either username
        email: string // or e-mail address
    }
    returns {
        errors: {
            username: 'Unknown Username', // on error
            email: 'Unknown Email' // on error
        }
        username: string // on success
    }
    see: requestToken
    '''
    user = None
    if 'username' in data:
        try:
            user = User.objects.get(username__iexact=data['username'])
        except User.DoesNotExist:
            user = None
    elif 'email' in data:
        try:
            user = User.objects.get(email__iexact=data['email'])
        except User.DoesNotExist:
            user = None
    if user:
        while True:
            code = ox.toAZ(random.randint(ox.fromAZ('AAAAAAAAAAAAAAAA'),
                                          ox.fromAZ('AAAAAAAAAAAAAAAAA')))
            if models.UserProfile.objects.filter(reset_code=code).count() == 0:
                break
        user_profile = user.get_profile()
        user_profile.reset_code = code 
        user_profile.save()

        template = loader.get_template('password_reset_email.txt')
        context = RequestContext(request, {
            'code': code,
            'sitename': settings.SITENAME,
            'footer': settings.CONFIG['site']['email']['footer'],
            'url': request.build_absolute_uri('/'),
        })
        message = template.render(context)
        subject = '%s - Reset Password' % settings.SITENAME
        user.email_user(subject, message)
        response = json_response({
            'username': user.username
        }, text='password reset email sent')
    else:
        response = json_response({
            'errors': {
            }
        })
        if 'username' in data:
            response['data']['errors']['username'] = 'Unknown Username'
        elif 'email' in data:
            response['data']['errors']['email'] = 'Unknown Email'
        else:
            response = json_response(status=400, text='invalid data')
    return render_to_json_response(response)
actions.register(requestToken, cache=False)


@capability_required_json('canManageUsers')
def editUser(request, data):
    '''
    Edits a user
    takes {
        id: string, // user id
        key: value, // property id and new value
        ... // more key/value pairs
    }
    returns {}
    notes: Possible keys are 'email', 'id', 'level', 'notes', 'username'
    see: removeUser
    '''
    response = json_response()
    user = get_object_or_404_json(User, pk=ox.fromAZ(data['id']))

    profile = user.get_profile()
    if 'disabled' in data:
        user.is_active = not data['disabled']
    if 'email' in data:
        if 'email' in data:
            data['email'] = ox.escape_html(data['email'])
        if User.objects.filter(email__iexact=data['email']).exclude(id=user.id).count()>0:
            response = json_response(status=403, text='email already in use')
            return render_to_json_response(response)
        user.email = data['email']
    if 'level' in data:
        profile.set_level(data['level'])
    if 'notes' in data:
        profile.notes = data['notes']
    if 'newsletter' in data:
        profile.newsletter = data['newsletter']
    if 'groups' in data:
        groups = data['groups']
        if isinstance(groups, list):
            groups = filter(lambda g: g.strip(), groups)
            groups = [ox.escape_html(g) for g in groups]
            for g in user.groups.exclude(name__in=groups):
                user.groups.remove(g)
            current_groups = [g.name for g in user.groups.all()]
            for g in filter(lambda g: g not in current_groups, groups):
                group, created = Group.objects.get_or_create(name=g) 
                user.groups.add(group)
    if 'username' in data:
        if User.objects.filter(
                username__iexact=data['username']).exclude(id=user.id).count()>0:
            response = json_response(status=403, text='username already in use')
            return render_to_json_response(response)
        user.username = data['username']
    user.save()
    profile.save()
    add_changelog(request, data, user.username)
    response['data'] = user.data.get().json()
    return render_to_json_response(response)
actions.register(editUser, cache=False)


@capability_required_json('canManageUsers')
def removeUser(request, data):
    '''
    Removes a user
    takes {
        username: string // username
    }
    returns {}
    notes: Note that this will only disable the user account -- annotations
    will not be removed.
    see: editUser, findUser
    '''
    response = json_response()
    u = get_user_or_404(data)
    add_changelog(request, data, u.username)
    u.delete()
    return render_to_json_response(response)
actions.register(removeUser, cache=False)


def findUser(request, data):
    '''
    Finds users for a given query
    takes {
        key: string, // username, email
        value: string, // search string
        operator: "==" // "==" or "="
        keys: [string] // list of properties to return
    }
    returns {
        users: [object] // list of users
    }
    notes: Possible keys ... undocumented
    see: editUser, removeUser
    '''
    response = json_response(status=200, text='ok')
    #keys = data.get('keys')
    #if not keys:
    #    keys = ['username', 'level']
    keys = ['username', 'level']

    if settings.AUTH_CHECK_USERNAME:
        if data['key'] == 'email':
            response['data']['users'] = [models.user_json(u, keys)
                                         for u in User.objects.filter(email__iexact=data['value'])]
        else:
            response['data']['users'] = [models.user_json(u, keys)
                                         for u in User.objects.filter(username__iexact=data['value'])]
    else:
        response['data']['users'] = [{'username': data['value'], 'level': 'member'}]
    return render_to_json_response(response)
actions.register(findUser)


def parse_query(data, user):
    query = {}
    query['range'] = [0, 100]
    query['sort'] = [{'key':'username', 'operator':'+'}]
    for key in ('keys', 'range', 'sort', 'query'):
        if key in data:
            query[key] = data[key]
    query['qs'] = models.SessionData.objects.find(query, user)
    return query


def order_query(qs, sort):
    order_by = []
    for e in sort:
        operator = e['operator']
        if operator != '-':
            operator = ''
        key = {
            'browser': 'browser',
            'email': 'user__email',
            'firstseen': 'firstseen',
            'groups': 'groupssort',
            'ip': 'ip',
            'lastseen': 'lastseen',
            'level': 'level',
            'location': 'location_sort',
            'screensize': 'screensize',
            'system': 'system',
            'timesseen': 'timesseen',
            'useragent': 'useragent',
            'user': 'username',
            'username': 'username',
            'numberoflists': 'numberoflists',
            'windowsize': 'windowsize',
        }.get(e['key'], 'user__profile__%s'%e['key'])
        order = '%s%s' % (operator, key)
        order_by.append(order)
    if order_by:
        qs = qs.order_by(*order_by, nulls_last=True)
    return qs


@capability_required_json('canManageUsers')
def findUsers(request, data):
    '''
        takes {
            query: {
                conditions: [
                    {
                        key: 'user',
                        value: 'something',
                        operator: '='
                    }
                ]
                operator: ","
            },
            sort: [{key: 'username', operator: '+'}],
            range: [0, 100]
            keys: []
        }

        possible query keys:
            username, email, lastLogin, browser, groups
        
        returns {
            items: [
                {name:, user:, featured:, public...}
            ]
        }

        takes {
            query: query,
            sort: array,
            range: array
        }

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

        with keys, items is list of dicts with requested properties:
        returns {
            items: [object]
        }

Positions
        takes {
            query: query,
            positions: []
        }

            query: query object, more on query syntax at
                   https://wiki.0x2620.org/wiki/pandora/QuerySyntax
            positions:  ids of places for which positions are required
    see: editUser
    '''
    response = json_response(status=200, text='ok')
    query = parse_query(data, request.user)
    qs = order_query(query['qs'], query['sort'])
    if 'keys' in data:
        qs = qs[query['range'][0]:query['range'][1]]
        response['data']['items'] = [p.json(data['keys'], request.user) for p in qs]
    elif 'position' in query:
        ids = [i.get_id() for i in qs]
        data['conditions'] = data['conditions'] + {
            'value': data['position'],
            'key': query['sort'][0]['key'],
            'operator': '^'
        }
        query = parse_query(data, request.user)
        qs = order_query(query['qs'], query['sort'])
        if qs.count() > 0:
            response['data']['position'] = utils.get_positions(ids, [qs[0].public_id])[0]
    elif 'positions' in data:
        ids = [i.get_id() for i in qs]
        response['data']['positions'] = utils.get_positions(ids, data['positions'])
    else:
        response['data']['items'] = qs.count()
        response['data']['users'] = qs.exclude(user=None).count()
        response['data']['robots'] = qs.filter(level=-1).count()
        response['data']['guests'] = qs.filter(level=0).count()
    return render_to_json_response(response)
actions.register(findUsers)


@capability_required_json('canManageUsers')
def getUser(request, data):
    '''
        takes {
            id: string or username: string,
            keys: []
        }
        returns {
            id: string,
            ...
        }
    '''
    response = json_response()
    u = get_user_or_404(data)
    response['data'] = u.data.get().json(data.get('keys', []), request.user)
    return render_to_json_response(response)
actions.register(getUser)

@login_required_json
def mail(request, data):
    '''
        takes {
            to: [string], // array of usernames to send mail to
            subject: string,
            message: string
        }

        message can contain {username} or {email},
        this will be replace with the user/email
        the mail is sent to.

        returns {
        }
    '''
    response = json_response()
    p = request.user.get_profile()
    if p.capability('canSendMail'):
        email_from = '"%s" <%s>' % (settings.SITENAME, settings.CONFIG['site']['email']['system'])
        headers = {
            'Reply-To': settings.CONFIG['site']['email']['contact']
        }
        subject = data.get('subject', '').strip()
        users = [User.objects.get(username=username) for username in data['to']]
        for user in users:
            if user.email:
                message = data['message']
                for key, value in (
                    ('{username}', user.username),
                    ('{email}', user.email),
                ):
                    message = message.replace(key, value)
                email_to = '"%s" <%s>' % (user.username, user.email)
                email = EmailMessage(subject,
                                     message,
                                     email_from,
                                     [email_to],
                                     headers = headers)
                email.send(fail_silently=True)
        if 'receipt' in data \
            and data['receipt']:
            template = loader.get_template('mailout_receipt.txt')
            context = RequestContext(request, {
                'footer': settings.CONFIG['site']['email']['footer'],
                'to': ', '.join(['"%s" <%s>' % (u.username, u.email) for u in users]),
                'subject': subject,
                'message': data['message'],
                'url': request.build_absolute_uri('/'),
            })
            message = template.render(context)
            subject = u'Fwd: %s' % subject
            email_to = '"%s" <%s>' % (request.user.username, request.user.email)
            receipt = EmailMessage(subject,
                                   message,
                                   email_from,
                                   [email_to])
            receipt.send(fail_silently=True)
        response = json_response(text='message sent')
    else:
        response = json_response(status=403, text='not allowed to send mail')
    return render_to_json_response(response)
actions.register(mail, cache=False)

def contact(request, data):
    '''
    Sends a message to the contact address
    takes {
        email: string,
        subject: string,
        message: string
    }
    returns {
    }
    '''
    name = data.get('name', '')
    email = data.get('email', '')
    if request.user.is_authenticated():
        if not name:
            name = request.user.username
        if not email:
            email = request.user.email
    if 'message' in data and data['message'].strip():
        email_from = '"%s" <%s>' % (settings.SITENAME, settings.CONFIG['site']['email']['system'])
        email_to = [settings.CONFIG['site']['email']['contact'], ]
        subject = data.get('subject', '').strip()
        template = loader.get_template('contact_email.txt')
        context = RequestContext(request, {
            'name': name,
            'email': email,
            'subject': subject,
            'message': ox.decode_html(data['message']).strip(),
            'sitename': settings.SITENAME,
            'footer': settings.CONFIG['site']['email']['footer'],
            'url': request.build_absolute_uri('/'),
        })
        subject = ox.decode_html(subject)
        message = ox.decode_html(template.render(context))
        response = json_response(text='message sent')
        try:
            send_mail(u'%s Contact - %s' % (settings.SITENAME, subject), message, email_from, email_to)
        except BadHeaderError:
            response = json_response(status=400, text='invalid data')
        if request.user.is_authenticated() \
            and 'receipt' in data \
            and data['receipt']:
            template = loader.get_template('contact_receipt.txt')
            context = RequestContext(request, {
                'name': name,
                'from': email,
                'sitename': settings.SITENAME,
                'footer': settings.CONFIG['site']['email']['footer'],
                'to': email_to[0],
                'subject': subject,
                'message': data['message'].strip(),
                'url': request.build_absolute_uri('/'),
            })
            message = template.render(context)
            try:
                send_mail('Fwd: %s' % subject, message, email_from, [email])
            except:
                pass
    else:
        response = json_response(status=400, text='invalid data')
    return render_to_json_response(response)
actions.register(contact, cache=False)


def getPositionById(list, key):
    for i in range(0, len(list)):
        if list[i]['id'] == key:
            return i
    return -1


@login_required_json
def editPreferences(request, data):
    '''
    Edits the current user's preferences
    takes {
        key: value
    }
    keys: email, password
    returns {}
    '''
    errors = {}
    change = False
    response = json_response()
    if 'email' in data:
        if User.objects.filter(
                email=data['email']).exclude(username=request.user.username).count()>0:
            errors['email'] = 'Email address already in use'
        else:
            change = True
            request.user.email = ox.escape_html(data['email'])
    if 'newsletter' in data:
        profile = request.user.get_profile()
        profile.newsletter = data['newsletter']
        profile.save()
    if 'password' in data:
        change = True
        request.user.set_password(data['password'])
    if change:
        request.user.save()
    if errors:
        response = json_response({ 'errors': errors})
    return render_to_json_response(response)
actions.register(editPreferences, cache=False)


def reset_ui(request):
    if request.user.is_authenticated():
        profile = request.user.get_profile()
        profile.ui = {}
        profile.save()
    else:
        request.session['ui'] = '{}'
    return redirect('/')


def resetUI(request, data):
    '''
    Resets the user's UI settings to the default state
    takes {}
    returns {}
    see: setUI
    '''
    response = json_response()
    if request.user.is_authenticated():
        profile = request.user.get_profile()
        profile.ui = {}
        profile.save()
    else:
        request.session['ui'] = '{}'
    return render_to_json_response(response)
actions.register(resetUI, cache=False)


def setUI(request, data):
    '''
    Sets one or more UI settings for the current user
    takes {
        key: value, // property and new value
        ... // more key/value pairs
    }
    returns {}
    notes: To set nested keys, use {'foo.bar.baz': value}
    see: resetUI
    '''
    if request.user.is_authenticated():
        profile = request.user.get_profile()
        ui = profile.ui
    else:
        ui = json.loads(request.session.get('ui', '{}'))
    for key in data:
        keys = map(lambda p: p.replace('\0', '\\.'), key.replace('\\.', '\0').split('.'))
        value = data[key]
        p = ui
        while len(keys)>1:
            key = keys.pop(0)
            if isinstance(p, list):
                p = p[getPositionById(p, key)]
            else:
                if key not in p:
                    p[key] = {}
                p = p[key]
        if value == None and keys[0] in p:
            del p[keys[0]]
        else:
            p[keys[0]] = value
    if request.user.is_authenticated():
        profile.save()
    else:
        request.session['ui'] = json.dumps(ui)

    if data.get('item'):
        item = get_object_or_404_json(Item, public_id=data['item'])
        if request.user.is_authenticated():
            access, created = Access.objects.get_or_create(item=item, user=request.user)
        else:
            access, created = Access.objects.get_or_create(item=item, user=None)
        if not created:
            access.save()

    response = json_response()
    return render_to_json_response(response)
actions.register(setUI, cache=False)


@capability_required_json('canManageUsers')
def statistics(request, data):
    '''
    Gets usage statistics
    takes {}
    returns {
        ... // undocumented
    }
    '''
    response = json_response()
    from app.models import Settings
    stats = Settings.get('statistics')
    if not stats:
        import tasks
        tasks.update_statistics()
        stats = Settings.get('statistics')
    response['data'] = stats
    return render_to_json_response(response)
actions.register(statistics, cache=False)


def group_json(g):
    return {
        'id': ox.toAZ(g.id),
        'name': g.name,
        'users': g.user_set.count(),
        'items': g.items.count(),
    }


@login_required_json
def getGroups(request, data):
    '''
    Gets user groups
    takes {}
    returns {
        groups: [
            {id: string, name: string, users: int, items: int}
        ]
    }
    see: addGroup, editGroup, getGroups, removeGroup
    '''
    response = json_response(status=200, text='ok')
    response['data']['groups'] = []
    for g in Group.objects.all().order_by('name'):
        response['data']['groups'].append(group_json(g))
    return render_to_json_response(response)
actions.register(getGroups)


@login_required_json
def getGroup(request, data):
    '''
    Gets user group
    takes {
        id: string
            or
        name: string
    }
    returns {
        id: string,
        name: string
        users: int
        items: int
    }
    see: addGroup, editGroup, getGroups, removeGroup
    '''
    response = json_response(status=200, text='ok')
    g = get_group_or_404(data)
    response['data'] = group_json(g)
    return render_to_json_response(response)
actions.register(getGroup, cache=False)


@capability_required_json('canManageUsers')
def addGroup(request, data):
    '''
    Adds user group
    takes {
        name: string
    }
    returns {
        id: string,
        name: string
        users: int
        items: int
    }
    see: editGroup, getGroup, getGroups, removeGroup
    '''
    response = json_response(status=200, text='ok')
    created = False
    n = 1
    name = data['name']
    _name = re.sub(' \[\d+\]$', '', name).strip()
    while not created:
        g, created = Group.objects.get_or_create(name=name)
        n += 1
        name = u'%s [%d]' % (_name, n) 
    response['data'] = group_json(g)
    add_changelog(request, data, g.name)
    return render_to_json_response(response)
actions.register(addGroup, cache=False)


@capability_required_json('canManageUsers')
def editGroup(request, data):
    '''
    Edits user group
    takes {
        id: string,
        name: string
        
    }
    returns {
        name: string
        users: int
    }
    see: addGroup, getGroup, getGroups, removeGroup
    '''
    response = json_response(status=200, text='ok')
    g = Group.objects.get(id=ox.fromAZ(data['id']))
    g.name = data['name']
    g.save()
    add_changelog(request, data, g.name)
    response['data'] = group_json(g)
    return render_to_json_response(response)
actions.register(editGroup, cache=False)


@capability_required_json('canManageUsers')
def removeGroup(request, data):
    '''
    Removes user group
    takes {
        id: string
    }
    returns {
    }
    see: addGroup, editGroup, getGroup, getGroups
    '''
    response = json_response(status=200, text='ok')
    g = get_group_or_404(data)
    for i in g.items.all():
        i.groups.remove(g)
    for u in g.user_set.all():
        u.groups.remove(g)
    add_changelog(request, data, g.name)
    g.delete()
    return render_to_json_response(response)
actions.register(removeGroup, cache=False)
