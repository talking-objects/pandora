# -*- coding: utf-8 -*-
from django.db.models import Q, Manager
from django.conf import settings

from oxdjango.managers import get_operator
from oxdjango.query import QuerySet

keymap = {
    'email': 'user__email',
    'user': 'username',
    'group': 'user__groups__name',
    'groups': 'user__groups__name',
}
default_key = 'username'

def parseCondition(condition, user):
    k = condition.get('key', default_key)
    k = keymap.get(k, k)
    v = condition['value']
    op = condition.get('operator')
    if not op:
        op = '='
    if op.startswith('!'):
        op = op[1:]
        exclude = True
    else:
        exclude = False

    if k == 'level':
        levels = ['robot'] + settings.CONFIG['userLevels']
        if v in levels:
            v = levels.index(v) - 1
        else:
            v = 0
        key = k + get_operator(op, 'int')
    else:
        key = k + get_operator(op, 'istr')
    key = str(key)
    q = Q(**{key: v})
    if exclude:
        q = ~q
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

class SessionDataManager(Manager):

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
        qs = qs.distinct()
        return qs
