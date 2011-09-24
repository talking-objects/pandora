# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from django.contrib.auth.models import User

from django.db.models import Q

def parseCondition(condition, user):
    k = condition.get('key', 'name')
    k = {
        'user': 'user__username',
    }.get(k, k)
    v = condition['value']
    op = condition.get('operator')
    if not op:
        op = '='
    if op.startswith('!'):
        op = op[1:]
        exclude = True
    else:
        exclude = False

    key = '%s%s' % (k, {
        '==': '__iexact',
        '^': '__istartswith',
        '$': '__iendswith',
    }.get(op,'__icontains'))

    key = str(key)
    if exclude:
        q = ~Q(**{k: v})
    else:
        q = Q(**{k: v})
    return q

def parseConditions(conditions, operator, user):
    '''
    conditions: [
    ],
    operator: "&"
    '''
    conn = []
    for condition in conditions:
        if 'conditions' in condition:
            q = parseConditions(condition['conditions'],
                             condition.get('operator', '&'), user)
            if q:
                conn.append(q)
            pass
        else:
            if condition.get('value', '') != '' or \
               condition.get('operator', '') == '=':
                conn.append(parseCondition(condition, user))
    if conn:
        q = conn[0]
        for c in conn[1:]:
            if operator == '|':
                q = q | c
            else:
                q = q & c
        return q
    return None

def find_user(data, user):
    qs = User.objects.all()
    query = data.get('query', {})
    conditions = parseConditions(query.get('conditions', []),
                                 query.get('operator', '&'),
                                 user)
    if conditions:
        qs = qs.filter(conditions)
    return qs
