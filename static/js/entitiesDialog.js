'use strict';

(function() {

// cribbed from documentsPanel.js, TODO: refactor
var entitiesInput = function(width, defaultType, max) {
    var labelWidth = 80;

    if (!defaultType) {
        defaultType = pandora.site.entities[0].id;
    }

    return Ox.ArrayInput({
            input: {
                get: function(width) {
                    var $input = Ox.FormElementGroup({
                        elements: [
                            Ox.Select({
                                items: pandora.site.entities.map(function(entity) {
                                    return {
                                        id: entity.id,
                                        title: entity.title
                                    };
                                }),
                                overlap: 'right',
                                width: labelWidth
                            })
                            .bindEvent({
                                change: function() {
                                    var v = $input.value();
                                    $input.value({type: v.type, name: ''});
                                    $input.options('elements')[1].focusInput();
                                }
                            }),
                            Ox.Input({
                                autocomplete: function(value, callback) {
                                    pandora.api.autocompleteEntities({
                                        key: $input.value().type,
                                        operator: '=',
                                        range: [0, 10],
                                        value: value
                                    }, function(result) {
                                        callback(result.data.items);
                                    });
                                },
                                autocompleteReplace: true,
                                autocompleteSelect: true,
                                autocompleteSelectSubmit: true,
                                width: width - labelWidth
                            })
                        ],
                        width: width,
                        split: function(value) {
                            return [value.type || defaultType, value.name || ''];
                        },
                        join: function(value) {
                            return {type: value[0], name: value[1]};
                        }
                    });
                    return $input;
                },
                getEmpty: function(value) {
                    var type = (value && value[0]) || defaultType;
                    return {type: type, name: ''};
                },
                isEmpty: function(value) {
                    return !value.name;
                },
                setWidth: function($input, width) {
                    $input.options('elements')[1].options({
                        width: width - labelWidth
                    });
                }
            },
            width: width,
            max: max || 0,
        });
}

pandora.ui.entitiesDialog = function(options) {

    var dialogHeight = Math.round((window.innerHeight - 48) * 0.9),
        dialogWidth = Math.round(window.innerWidth * 0.9),

        ui = pandora.user.ui,
        type = ui.entitiesType || (
            pandora.site.entities.length ? pandora.site.entities[0].id : ''
        ),
        selected = ui.entitiesSelection[type] || [],

        $entitiesSelect = Ox.Select({
            items: pandora.site.entities.map(function(type) {
                return {
                    id: type.id,
                    title: type.title
                };
            }),
            value: type,
            width: 122
        })
        .bindEvent({
            change: function(data) {
                type = data.value;
                pandora.UI.set({entitiesType: type});
                $list.reloadList();
                selectEntities();
            }
        })
        .css({
            float: 'left',
            margin: '4px 2px 4px 4px'
        }),

        $findInput = Ox.Input({
            changeOnKeypress: true,
            clear: true,
            placeholder: 'Find',
            width: 122
        })
        .css({
            float: 'right',
            margin: '4px 4px 4px 2px'
        })
        .bindEvent({
            change: function(data) {
                $list.options({
                    query: {
                        conditions: data.value ? [
                            {key: '*', operator: '=', value: data.value}
                        ] : [],
                        operator: '&'
                    }
                });
            }
        }),

        $listBar = Ox.Bar({size: 24})
            .append($entitiesSelect)
            .append($findInput),

        $list = Ox.TableList({
            columns: [
                {
                    id: 'id',
                    title: 'ID',
                    operator: '+'
                },
                {
                    id: 'name',
                    title: 'Name',
                    operator: '+',
                    visible: true,
                    width: 256 - Ox.SCROLLBAR_SIZE
                }
            ],
            items: function(options, callback) {
                pandora.api.findEntities(Ox.extend(Ox.clone(options), {
                    query: {
                        conditions: [
                            {key: 'type', operator: '==', value: type}
                        ].concat(options.query.conditions),
                        operator: '&'
                    }
                }), callback);
            },
            sort: [{key: 'name', operator: '+'}],
            scrollbarVisible: true,
            selected: selected,
            unique: 'id',
            width: 256 - Ox.SCROLLBAR_SIZE
        })
        .bindEvent({
            add: function() {
                addEntity();
            },
            'delete': function() {
                deleteEntities();
            },
            init: function(data) {
                var text = Ox.formatCount(
                    data.items,
                    Ox._('entity'),
                    Ox._('entities')
                )
                $listStatus.html(text[0].toUpperCase() + text.slice(1));
            },
            select: function(data) {
                pandora.UI.set('entitiesSelection.' + type, data.ids);
            }
        }),

        $listStatus = Ox.Element()
        .css({
            fontSize: '9px',
            marginTop: '2px',
            textAlign: 'center'
        })
        .html(Ox._('Loading...')),

        $listStatusbar = Ox.Bar({size: 16})
            .append($listStatus),

        $listPanel = Ox.SplitPanel({
            elements: [
                {element: $listBar, size: 24},
                {element: $list},
                {element: $listStatusbar, size: 16}
            ],
            orientation: 'vertical'
        })
        .bindEvent({
            resize: updateList
        }),

        $entity = Ox.Element()
            .css({overflowY: 'auto'}),

        $itemMenu = Ox.MenuButton({
            items: [
                {
                    id: 'add',
                    title: Ox._('Add Entity'),
                    keyboard: 'control n'
                },
                {
                    id: 'delete',
                    title: Ox._('Delete Entity...'),
                    disabled: true,
                    keyboard: 'delete'
                }
            ],
            title: 'set',
            tooltip: Ox._('Options'),
            type: 'image'
        })
        .css({
            float: 'left',
            margin: '4px'
        })
        .bindEvent({
            click: function(data) {
                if (data.id == 'add') {
                    addEntity();
                } else if (data.id == 'delete') {
                    deleteEntities();
                }
            }
        }),

        $deselectButton = Ox.Button({
            title: 'close',
            tooltip: Ox._('Done'),
            type: 'image'
        })
        .css({
            float: 'right',
            margin: '4px'
        })
        .hide()
        .bindEvent({
            click: function() {
                pandora.UI.set('entitiesSelection.' + type, []);
            }
        }),

        $itemBar = Ox.Bar({size: 24})
            .append($itemMenu)
            .append($deselectButton),

        $labels = [],

        $inputs = [],

        $form = Ox.Element()
        .css({
            overflowY: 'scroll',
            padding: '4px'
        }),

        $itemStatus = Ox.Element()
        .css({
            fontSize: '9px',
            marginTop: '2px',
            textAlign: 'center'
        }),

        $itemStatusbar = Ox.Bar({size: 16})
            .append($itemStatus),

        $itemPanel = Ox.SplitPanel({
            elements: [
                {element: $itemBar, size: 24},
                {element: $form},
                {element: $itemStatusbar, size: 16}
            ],
            orientation: 'vertical'
        })
        .bindEvent({
            resize: updateForm
        }),

        $content = pandora.site.entities.length ? Ox.SplitPanel({
            elements: [
                {
                    element: $listPanel,
                    resizable: true,
                    resize: [256, 384, 512],
                    size: 256
                },
                {
                    element: $entity
                },
                {
                    element: $itemPanel,
                    resizable: true,
                    resize: [256, 384, 512],
                    size: 256
                }
            ],
            orientation: 'horizontal'
        }) : Ox.Element()
            .css({
                fontSize: '12px',
                paddingTop: '32px',
                textAlign: 'center'
            })
            .html(Ox._('No entities defined.')),

        that = Ox.Dialog({
            buttons: [
                Ox.Button({
                    title: Ox._('Manage Documents...')
                })
                .bindEvent({
                    click: function() {
                        that.close();
                        (pandora.$ui.documentsDialog || (
                            pandora.$ui.documentsDialog = pandora.ui.documentsDialog()
                        )).open();
                    }
                }),
                {},
                Ox.Button({
                    title: Ox._('Done'),
                    width: 48
                })
                .bindEvent({
                    click: function() {
                        that.close();
                    }
                })
            ],
            closeButton: true,
            content: $content,
            height: dialogHeight,
            maximizeButton: true,
            minHeight: 256,
            minWidth: 512,
            padding: 0,
            removeOnClose: true,
            title: Ox._('Manage Entities'),
            width: dialogWidth
        })
        .bindEvent({
            // resize: ...
            pandora_entitiesselection: function() {
                selectEntities();
            },
            pandora_entitiestype: function() {
                type = ui.entitiesType || (
                    pandora.site.entities.length ? pandora.site.entities[0].id : ''
                );
                $entitiesSelect.options({value: type});
                $list.reloadList();
                selectEntities();
            }
        });

    that.superClose = that.close;
    that.close = function() {
        Ox.Request.clearCache('findEntities');
        that.superClose();
        delete pandora.$ui.entitiesDialog;
    };

    selectEntities();

    function addEntity() {
        pandora.api.addEntity({
            type: type
        }, function(result) {
            Ox.Request.clearCache('findEntities');
            $list.reloadList();
            pandora.UI.set('entitiesSelection.' + type, [result.data.id]);
        });
    }

    function deleteEntities() {
        pandora.ui.deleteEntityDialog(
            $list.options('selected').map(function(id) {
                return $list.value(id);
            }),
            function() {
                Ox.Request.clearCache();
                $list.reloadList();
                pandora.UI.set('entitiesSelection.' + type, []);
            }
        ).open();
    }

    function renderEntity() {
        var id = ui.entitiesSelection[type]
            ? ui.entitiesSelection[type][0]
            : null;
        if (!id) {
            $entity.empty();
            return;
        }
        pandora.entity({
            id: id,
            type: type,
            view: 'entity'
        }, function(html) {
            if (id != ui.entitiesSelection[type][0]) {
                return;
            }
            $entity.html(html);
            pandora.createLinks($entity);
        });
    }

    function renderForm() {
        var id = ui.entitiesSelection[type]
                ? ui.entitiesSelection[type][0]
                : null,
            width = $content.options('elements')[2].size
                - 16 - Ox.SCROLLBAR_SIZE;
        if (!id) {
            $form.empty();
            return;
        }
        pandora.api.getEntity({
            id: id
        }, function(result) {
            if (id != ui.entitiesSelection[type][0]) {
                return;
            }
            var keys = Ox.getObjectById(pandora.site.entities, type).keys;
            $form.empty()
            keys.forEach(function(key, index) {
                var defaultValue = void 0,
                    value = result.data[key.id],
                    $label = Ox.Label({
                            title: Ox._(key.title),
                            width: width
                        })
                        .css({
                            margin: (index == 0 ? 4 : 16) + 'px 4px 8px 4px'
                        })
                        .appendTo($form),
                    $input;
                if (key.type === 'document') {
                    $input = Ox.Input({autovalidate: /^[A-Z]+?$/});
                } else if (key.type === 'float') {
                    $input = Ox.Input({type: 'float'});
                } else if (key.type === 'int') {
                    $input = Ox.Input({type: 'int'});
                } else if (key.type === 'string') {
                    $input = Ox.Input();
                } else if (key.type[0] === 'string') {
                    $input = Ox.ArrayInput();
                    defaultValue = [];
                } else if (key.type === 'text') {
                    $input = Ox.Input({
                        height: width,
                        type: 'textarea'
                    });
                } else if (key.type[0] === 'entity') {
                    $input = entitiesInput(width, type, key.max || 0);
                    defaultValue = [];

                    $input.bindEvent({
                        submit: function(data) {
                            $input.triggerEvent('change', data);
                        }
                    })
                }

                var change = function(data, eventName) {
                    console.log(eventName, data);
                    pandora.api.editEntity(Ox.extend({
                        id: id
                    }, key.id, data.value), function(result) {
                        Ox.Request.clearCache('findEntities');
                        Ox.Request.clearCache('getEntity');
                        if (key.id == 'name') {
                            $input.value(result.data.name);
                            $list.reloadList(true);
                        } else if (key.id == 'alternativeNames') {
                            $input.value(result.data.alternativeNames);
                        }
                        renderEntity();
                    });
                };

                $input.options({
                        disabled: key.id == 'id',
                        value: value || defaultValue,
                        width: width
                    })
                    .css({margin: '4px'})
                    .bindEvent({
                        change: change,
                    })
                    .appendTo($form);
                $labels.push($label);
                $inputs.push($input);
            });
        });
    }

    function selectEntities() {
        var entitiesLength = ui.entitiesSelection[type]
                ? ui.entitiesSelection[type].length
                : 0,
            text = Ox.formatCount(entitiesLength, Ox._('entity'), Ox._('entities'))
                + ' ' + Ox._('selected');
        $list.options({selected: ui.entitiesSelection[type] || []})
        renderEntity();
        $itemMenu[
            entitiesLength ? 'enableItem' : 'disableItem'
        ]('delete');
        $itemMenu.setItemTitle('delete', Ox._('Delete {0}...', [
            Ox._(entitiesLength < 2 ? 'Entity' : 'Entities')
        ]));
        $deselectButton[entitiesLength ? 'show' : 'hide']();
        renderForm();
        $itemStatus.html(text[0].toUpperCase() + text.slice(1));
    }

    function updateForm() {
        var width = $content.options('elements')[2].size - 16 - Ox.SCROLLBAR_SIZE;
        $labels.forEach(function($label) {
            $label.options({width: width});
        });
        $inputs.forEach(function($input) {
            $input.options({width: width});
        });
    }

    function updateList() {
        var width = $content.options('elements')[0].size;
        $entitiesSelect.options({width: Math.ceil((width - 12) / 2)});
        $findInput.options({width: Math.floor((width - 12) / 2)});
        $list.size();
    }

    return that;

};
}());
