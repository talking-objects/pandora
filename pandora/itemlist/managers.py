# -*- coding: utf-8 -*-

from django.db.models import Q, Manager

from oxdjango.managers import get_operator
from oxdjango.query import QuerySet

keymap = {
    'user': 'user__username',
}
default_key = 'name'

def parseCondition(condition, user):
    '''
    '''
    k = condition.get('key', default_key)
    k = keymap.get(k, k)
    if not k:
        k = default_key
    v = condition.get('value', '')
    op = condition.get('operator')
    if not op:
        op = '='
    if op.startswith('!'):
        op = op[1:]
        exclude = True
    else:
        exclude = False
    if k == 'id':
        v = v.split(":")
        if len(v) >= 2:
            v = (v[0], ":".join(v[1:]))
            q = Q(user__username=v[0], name=v[1])
        else:
            q = Q(id__in=[])
        return q
    if k == 'subscribed':
        key = 'subscribed_users__username'
        v = user.username
    elif isinstance(v, bool):
        key = k
    else:
        key = k + get_operator(op, 'istr')
    key = str(key)
    if exclude:
        q = ~Q(**{key: v})
    else:
        q = Q(**{key: v})
    return q

def parseConditions(conditions, operator, user):
    '''
    conditions: [
        {
            value: "war"
        }
        {
            key: "year",
            value: "1970-1980,
            operator: "!="
        },
        {
            key: "country",
            value: "f",
            operator: "^"
        }
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


class ListManager(Manager):

    def get_query_set(self):
        return QuerySet(self.model)

    def find(self, data, user):
        '''
            query: {
                conditions: [
                    {
                        value: "war"
                    }
                    {
                        key: "year",
                        value: "1970-1980,
                        operator: "!="
                    },
                    {
                        key: "country",
                        value: "f",
                        operator: "^"
                    }
                ],
                operator: "&"
            }
        '''

        #join query with operator
        qs = self.get_query_set()
        query = data.get('query', {})
        conditions = parseConditions(query.get('conditions', []),
                                     query.get('operator', '&'),
                                     user)
        if conditions:
            qs = qs.filter(conditions)

        if user.is_anonymous:
            qs = qs.filter(Q(status='public') | Q(status='featured'))
        else:
            qs = qs.filter(Q(status='public') | Q(status='featured') | Q(user=user))
        return qs
