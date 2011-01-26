# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
import sys
import inspect

from django.conf import settings

from ox.django.shortcuts import render_to_json_response, json_response
from ox.utils import json


def autodiscover():
    #register api actions from all installed apps
    from django.utils.importlib import import_module
    from django.utils.module_loading import module_has_submodule
    for app in settings.INSTALLED_APPS:
        if app != 'api':
            mod = import_module(app)
            try:
                import_module('%s.views'%app)
            except:
                if module_has_submodule(mod, 'views'):
                    raise

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


class ApiActions(dict):
    properties = {}
    def __init__(self):

        def api(request):
            '''
                returns list of all known api actions
                param data {
                    docs: bool
                }
                if docs is true, action properties contain docstrings
                return {
                    status: {'code': int, 'text': string},
                    data: {
                        actions: {
                            'api': {
                                cache: true,
                                doc: 'recursion'
                            },
                            'hello': {
                                cache: true,
                                ..
                            }
                            ...
                        }
                    }
                }
            '''
            data = json.loads(request.POST.get('data', '{}'))
            docs = data.get('docs', False)
            code = data.get('code', False)
            _actions = self.keys()
            _actions.sort()
            actions = {}
            for a in _actions:
                actions[a] = self.properties[a]
                if docs:
                    actions[a]['doc'] = self.doc(a)
                if code:
                    actions[a]['code'] = self.code(a)
            response = json_response({'actions': actions})
            return render_to_json_response(response)
        self.register(api)

    def doc(self, f):
        return trim(self[f].__doc__)

    def code(self, name):
        f = self[name]
        if name != 'api' and hasattr(f, 'func_closure') and f.func_closure:
            f = f.func_closure[0].cell_contents 
        filename = f.func_code.co_filename[len(settings.PROJECT_ROOT)+1:]
        return filename, trim(inspect.getsource(f))

    def register(self, method, action=None, cache=True):
        if not action:
            action = method.func_name
        self[action] = method
        self.properties[action] = {'cache': cache}

    def unregister(self, action):
        if action in self:
            del self[action]

actions = ApiActions()

