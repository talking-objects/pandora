'use strict';

pandora.ui.embedDialog = function(/*[url, ]callback*/) {

    if (arguments.length == 1) {
        var url, callback = arguments[0];
    } else {
        var url = arguments[0], callback = arguments[1];
    }

    var api = pandora.api,
        duration,
        formWidth = 612,
        iframeHeight = Ox.last(pandora.site.video.resolutions),
        iframeWidth = Math.round(iframeHeight * pandora.site.video.previewRatio),
        listWidth = 128 + Ox.UI.SCROLLBAR_SIZE,
        labelWidth = 192,
        positionPlaceholder = '00:00:00.000',
        sites = [pandora.site.site].concat(pandora.site.sites).map(function(site) {
            return {id: site.url, title: site.url, https: site.https};
        }),
        dialogWidth = listWidth + formWidth + 32 + Ox.UI.SCROLLBAR_SIZE,
        dialogHeight = 384,

        views = [
            {
                id: 'info',
                title: 'Info',
                description: 'Embed poster and basic metadata',
                inputs: ['item']
            },
            {
                id: 'video',
                title: 'Video',
                description: 'Embed a clip or a full video',
                inputs: [
                    'item', 'position', 'in', 'out', 'annotation', 'title',
                    'showTimeline', 'showAnnotations', 'matchRatio'
                ]
            },
            {
                id: 'timeline',
                title: 'Timeline',
                description: 'Embed a timeline',
                inputs: ['item', 'position', 'title']
            },
            {
                id: 'list',
                title: 'List',
                description: 'Embed list icon and description',
                inputs: ['list']
            },
            {
                id: 'grid',
                title: 'Grid',
                description: 'Embed movies as a grid',
                inputs: ['find', 'sort', 'title']
            },
            {
                id: 'map',
                title: 'Map',
                description: 'Embed a map view',
                inputs: ['find', 'sort', 'title']
            },
            {
                id: 'calendar',
                title: 'Calendar',
                description: 'Embed a calendar view',
                inputs: ['find', 'sort', 'title']
            },
            {
                id: 'document',
                title: 'Document',
                description: 'Embed a document',
                inputs: ['document']
            },
            {
                id: 'edit',
                title: 'Edit',
                description: 'Embed an edited video',
                inputs: [
                    'edit', 'position',
                    'showTimeline', 'showAnnotations', 'matchRatio'
                ]
            },
            {
                id: 'text',
                title: 'Text',
                description: 'Embed text icon and description',
                inputs: ['text']
            }
        ].map(function(item, index) {
            return Ox.extend(item, {index: index});
        }),

        viewInputs = Ox.unique(Ox.flatten(views.map(function(view) {
            return view.inputs;
        }))),

        $list = Ox.TableList({
            columns: [
                {
                    id: 'title',
                    visible: true,
                    width: 128 - Ox.UI.SCROLLBAR_SIZE
                }
            ],
            items: views,
            max: 1,
            min: 1,
            scrollbarVisible: true,
            selected: ['info'],
            sort: [{key: 'index', operator: '+'}],
            unique: 'id'
        })
        .bindEvent({
            select: function() {
                updateHTML();
                updateForm();
            }
        }),

        $input = {
            advanced: Ox.Checkbox({
                    title: Ox._('Show Advanced Options'),
                    value: pandora.user.ui.showAdvancedEmbedOptions
                })
                .css({float: 'left', margin: '4px'})
                .bindEvent({
                    change: function(data) {
                        pandora.UI.set({showAdvancedEmbedOptions: data.value});
                        updateForm();
                    }
                })
        },

        $form = getForm(),

        $panel = Ox.SplitPanel({
            elements: [
                {element: $list, size: 128 + Ox.UI.SCROLLBAR_SIZE},
                {element: $form}
            ],
            orientation: 'horizontal'
        }),

        that = Ox.Dialog({
            buttons: [
                Ox.Button({
                        id: 'cancel',
                        title: Ox._('Cancel'),
                        width: 64
                    })
                    .bindEvent({
                        click: function() {
                            that.close();
                        }
                    }),
                Ox.Button({
                        id: 'insert',
                        title: Ox._('Insert'),
                        width: 64
                    })
                    .bindEvent({
                        click: function() {
                            callback($input.url.options('value'));
                            that.close();
                        }
                    })
            ],
            closeButton: true,
            content: $panel,
            fixedSize: true,
            height: dialogHeight,
            removeOnClose: true,
            title: Ox._('Embed'),
            width: dialogWidth
        });

    $($input.advanced.find('.OxButton')[0]).css({margin: 0});
    $(that.find('.OxBar')[1]).append($input.advanced);

    function formatHTML() {
        var type = $input.type.value();
        return type == 'link'
            ? '<a href="' + formatURL()
                + '">' + $input.text.value()
                + '</a>'
            : '<iframe src="' + formatURL()
                + '" width="' + $input.width.value()
                + '" height="' + $input.height.value()
                + '" frameborder="0" allowfullscreen></iframe>';
    }

    function formatURL() {
        var data = Ox.map($input, function($element) {
                return $element.value ? $element.value() : void 0;
            }),
            type = data.type,
            view = $list.options('selected')[0],
            options = Ox.serialize({
                title: data.title || void 0,
                showTimeline: data.showTimeline || void 0,
                timeline: data.timeline && data.timeline != 'default' ? data.timeline : void 0,
                showAnnotations: data.showAnnotations || void 0,
                showLayers: data.showAnnotations && data.showLayers ? data.showLayers : void 0,
                matchRatio: Ox.contains(['video', 'edit'], view) ? data.matchRatio || void 0 : void 0
            }, true),
            position = (
                data.position ? [data.position] : []
            ).concat(
                data['in'] || data.out ? [data['in'], data.out] : []
            ).join(',')
            + data['annotation'] || '';
        return Ox.encodeHTMLEntities(
            (
                type == 'iframe'
                ? (pandora.site.site.https ? 'https' : 'http')
                    + '://' + pandora.site.site.url + '/'
                : '/'
            )
            + (
                Ox.contains(['info', 'video', 'timeline'], view) ? data.item
                : view == 'list' ? 'list==' + data.list
                : view == 'document' ? 'documents/' + data.document
                : view == 'edit' ? 'edits/' + data.edit
                : view == 'text' ? 'texts/' + data.text
                : ''
            )
            + (
                Ox.contains(['info', 'grid', 'map', 'calendar'], view)
                ? (view == 'info' ? '/' : '') + view
                : ''
            )
            + (
                Ox.contains(['grid', 'map', 'calendar'], view) ? '/' + data.sort : ''
            )
            + (position ? '/' + position : '')
            + '#embed'
            + (options ? '?' + options : '')
        ).replace(/ /g, '_');
    }

    function getDuration(item, callback) {
        api.get({
            id: item,
            keys: ['duration']
        }, function(result) {
            duration = result.data.duration;
            callback();
        });
    }

    function getForm() {

        var css = {display: 'inline-block', margin: '4px 0'},
            view = $list.options('selected')[0];

        $form = Ox.Element()
            .attr({id: 'form'})
            .css({padding: '16px', overflowY: 'auto'});

        space().html(Ox.getObjectById(views, view).description).appendTo($form);

        space().appendTo($form);

        $input.type = Ox.ButtonGroup({
                buttons: [
                    {id: 'link', title: 'Embed in Text Section', width: formWidth / 2, selected: true},
                    {id: 'iframe', title: 'Embed in External Site', width: formWidth / 2}
                ],
                selectable: true
            })
            .css(css)
            .bindEvent({
                change: function() {
                    updateHTML();
                    updateForm();
                }
            })
            .appendTo($form);

        $input.html = Ox.Input({
                height: 64,
                type: 'textarea',
                width: formWidth
            })
            .css(css)
            .bindEvent({
                change: function(data) {
                    // ...
                }
            })
            .appendTo($form);

        $input.text = Ox.Input({
                label: Ox._('Link Text'),
                labelWidth: labelWidth,
                width: formWidth,
                value: '...'
            })
            .addClass('link')
            .css(css)
            .bindEvent({
                change: function(data) {
                    $input.text.options({
                        value: Ox.sanitizeHTML(data.value).trim() || '...'
                    });
                    updateHTML();
                }
            })
            .appendTo($form);

        $input.size = Ox.FormElementGroup({
                elements: [
                    Ox.Label({
                        overlap: 'right',
                        textAlign: 'right',
                        title: Ox._('Frame Size'),
                        width: labelWidth
                    }),
                    Ox.InputGroup({
                        inputs: [
                            $input.width = Ox.Input({id: 'width', placeholder: 'Width', value: iframeWidth, width: (formWidth - labelWidth - 16) / 2}),
                            $input.height = Ox.Input({id: 'height', placeholder: 'Height', value: iframeHeight, width: (formWidth - labelWidth - 16) / 2})
                        ],
                        separators: [{title: '×', width: 16}]
                    })
                ]
            })
            .addClass('iframe')
            .css(css)
            .bindEvent({
                change: updateHTML
            })
            .appendTo($form);

        space().appendTo($form);

        $input.site = Ox.FormElementGroup({
                elements: [
                    Ox.Label({
                        overlap: 'right',
                        textAlign: 'right',
                        title: Ox._('Site'),
                        width: labelWidth
                    }),
                    $input.protocol = Ox.Select({
                        id: 'protocol',
                        items: [
                            {id: 'http', title: 'http://'},
                            {id: 'https', title: 'https://', disabled: !pandora.site.site.https}
                        ],
                        overlap: 'right',
                        value: pandora.site.site.https ? 'https' : 'http',
                        width: 80
                    }),
                    $input.hostname = Ox.SelectInput({
                        inputWidth: formWidth - labelWidth - 160,
                        id: 'hostname',
                        items: sites.concat([{id: 'other', title: Ox._('Other...')}]),
                        max: 1,
                        min: 1,
                        placeholder: 'example.com',
                        value: pandora.site.site.url,
                        width: formWidth - labelWidth - 80
                    })
                ]
            })
            .addClass('advanced')
            .css(css)
            .bindEvent({
                change: updateHTML
            })
            .appendTo($form);

        $input.item = Ox.Input({
                label: Ox._(pandora.site.itemName.singular),
                labelWidth: labelWidth,
                width: formWidth,
                value: 'XYZ'
            })
            .css(css)
            .bindEvent({
                change: updateHTML
            })
            .appendTo($form);

        $input.list = Ox.Input({
                label: Ox._('List'),
                labelWidth: labelWidth,
                width: formWidth,
                value: 'foo:bar'
            })
            .css(css)
            .bindEvent({
                change: updateHTML
            })
            .appendTo($form);

        $input.document = Ox.Input({
                label: Ox._('Document'),
                labelWidth: labelWidth,
                width: formWidth,
                value: 'XYZ'
            })
            .css(css)
            .bindEvent({
                change: updateHTML
            })
            .appendTo($form);

        $input.edit = Ox.Input({
                label: Ox._('Edit{noun}'),
                labelWidth: labelWidth,
                width: formWidth,
                value: 'foo:bar'
            })
            .css(css)
            .bindEvent({
                change: updateHTML
            })
            .appendTo($form);

        $input.text = Ox.Input({
                label: Ox._('Text'),
                labelWidth: labelWidth,
                width: formWidth,
                value: 'foo:bar'
            })
            .css(css)
            .bindEvent({
                change: updateHTML
            })
            .appendTo($form);

        $input.position = Ox.Input({
                label: Ox._('Position'),
                labelWidth: labelWidth,
                placeholder: positionPlaceholder,
                width: formWidth
            })
            .css(css)
            .bindEvent({
                change: function(data) {
                    var hasInAndOut = $input['in']
                        && $input['in'].options('value') !== '';
                    if (data.value) {
                        $input.position.options({
                            value: limitPoint(
                                data.value,
                                hasInAndOut ? $input['in'].options('value') : 0,
                                hasInAndOut ? $input.out.options('value') : duration
                            )
                        });
                    }
                    $input.annotation && $input.annotation.options({value: ''});
                    updateHTML()
                }
            })
            .appendTo($form);

        $input['in'] = Ox.Input({
                label: Ox._('In Point'),
                labelWidth: labelWidth,
                placeholder: positionPlaceholder,
                width: formWidth
            })
            .css(css)
            .bindEvent({
                change: function(data) {
                    if (data.value) {
                        $input['in'].options({
                            value: Ox.formatDuration(Ox.parseDuration(
                                limitPoint(data.value, 0, duration)
                            ))
                        });
                        if ($input.out.options('value') === '') {
                            $input.out.options({value: Ox.formatDuration(duration)});
                        } else if (
                            Ox.parseDuration($input.out.options('value'))
                            < Ox.parseDuration(data.value)
                        ) {
                            $input.out.options({value: data.value});
                        }
                        $input.annotation && $input.annotation.options({value: ''});
                    }
                    updateHTML();
                }
            })
            .appendTo($form);

        $input.out = Ox.Input({
                label: Ox._('Out Point'),
                labelWidth: labelWidth,
                placeholder: positionPlaceholder,
                width: formWidth
            })
            .css(css)
            .bindEvent({
                change: function(data) {
                    if (data.value) {
                        $input.out.options({
                            value: limitPoint(data.value, 0, duration)
                        });
                        if ($input['in'].options('value') === '') {
                            $input['in'].options({value: Ox.formatDuration(0)});
                        } else if (
                            Ox.parseDuration($input['in'].options('value'))
                            > Ox.parseDuration(data.value)
                        ) {
                            $input['in'].options({value: data.value});
                        }
                        $input.annotation && $input.annotation.options({value: ''});
                    }
                    updateHTML();
                }
            })
            .appendTo($form);

        $input.annotation = Ox.Input({
                label: Ox._('Annotation'),
                labelWidth: labelWidth,
                width: formWidth
            })
            .css(css)
            .bindEvent({
                change: function(data) {
                    ['position', 'in', 'out'].forEach(function(key) {
                        $input[key].options({value: ''});
                    });
                    updateHTML();
                }
            })
            .appendTo($form);

        $input.find = pandora.ui.filterForm({mode: 'embed'})
            .css(css)
            .appendTo($form);

        $input.sort = Ox.Select({
                items: (
                    Ox.contains(['map', 'calendar'], view)
                    ? pandora.site.clipKeys.map(function(key) {
                        return Ox.extend(Ox.clone(key), {
                            title: Ox._('Clip {0}', [Ox._(key.title)])
                        });
                    })
                    : []
                ).concat(
                    pandora.site.sortKeys.map(function(key) {
                        return Ox.extend(Ox.clone(key), {
                            title: Ox._(key.title)
                        });
                    })
                ),
                label: Ox._('Sort by'),
                labelWidth: labelWidth,
                width: formWidth
            })
            .addClass('advanced')
            .css(css)
            .bindEvent({
                change: updateHTML
            })
            .appendTo($form);

        $input.title = Ox.Input({
                label: Ox._('Title'),
                labelWidth: labelWidth,
                width: formWidth,
                value: ''
            })
            .addClass('advanced')
            .css(css)
            .bindEvent({
                change: updateHTML
            })
            .appendTo($form);

        $input.showTimeline = Ox.Checkbox({
                label: Ox._('Show Timeline'),
                labelWidth: labelWidth,
                value: false,
                width: formWidth
            })
            .addClass('advanced')
            .css(css)
            .bindEvent({
                change: function() {
                    updateForm();
                    updateHTML();
                }
            })
            .appendTo($form);

        $input.timeline = Ox.Select({
                items: [
                    {id: 'default', title: Ox._('Default')}
                ].concat(
                    pandora.site.timelines
                ),
                label: Ox._('Timeline'),
                labelWidth: labelWidth,
                value: 'default',
                width: formWidth
            })
            .addClass('advanced')
            .css(css)
            .bindEvent({
                change: updateHTML
            })
            .appendTo($form);

        $input.showAnnotations = Ox.Checkbox({
                label: Ox._('Show Annotations'),
                labelWidth: labelWidth,
                value: false,
                width: formWidth
            })
            .addClass('advanced')
            .css(css)
            .bindEvent({
                change: function() {
                    updateForm();
                    updateHTML();
                }
            })
            .appendTo($form);

        $input.showLayersLabel = Ox.Label({
                title: Ox._('Show Layers'),
                width: formWidth
            })
            .addClass('advanced')
            .css(css)
            .appendTo($form);

        $input.showLayers = Ox.CheckboxGroup({
                checkboxes: pandora.site.layers.map(function(layer) {
                    return {id: layer.id, title: layer.title};
                }),
                max: pandora.site.layers.length,
                min: 0,
                type: 'list',
                value: pandora.site.layers.map(function(layer) {
                    return layer.id;
                }),
                width: formWidth - labelWidth
            })
            .addClass('advanced')
            .css({display: 'inline-block', margin: '4px 0 4px ' + labelWidth + 'px'})
            .bindEvent({
                change: updateHTML
            })
            .appendTo($form);

        $input.matchRatio = Ox.Checkbox({
                label: Ox._('Match Video Ratio'),
                labelWidth: labelWidth,
                value: true,
                width: formWidth
            })
            .addClass('advanced')
            .css(css)
            .bindEvent({
                change: updateHTML
            })
            .appendTo($form);

        updateHTML();
        updateForm();

        function space() {
            return $('<div>').css({height: '16px', width: formWidth + 'px'});
        }

        return $form;

    }

    function getItem(callback) {
        api.find({
            keys: ['id', 'duration'],
            query: {conditions: [], operator: '&'},
            range: [0, 1],
            sort: [{key: 'id', operator: '+'}]
        }, function(result) {
            duration = result.data.items[0].duration;
            item = result.data.items[0].id;
            callback();
        });
    }

    function updateForm() {
        var advanced = $input.advanced.value(),
            type = $input.type.value(),
            view = $list.options('selected')[0];
        $form.find('.link')[type == 'link' ? 'show' : 'hide']();
        $form.find('.iframe')[type == 'iframe' ? 'show' : 'hide']();
        viewInputs.forEach(function(id) {
            $input[id][
                Ox.contains(Ox.getObjectById(views, view).inputs, id)
                && (advanced || !$input[id].is('.advanced'))  ? 'show' : 'hide'
            ]();
        });
        $input.timeline[
            advanced && view == 'video' && $input.showTimeline.options('value') ? 'show' : 'hide'
        ]();
        $input.showLayersLabel[
            advanced && view == 'video' && $input.showAnnotations.options('value') ? 'show' : 'hide'
        ]();
        $input.showLayers[
            advanced && view == 'video' && $input.showAnnotations.options('value') ? 'show' : 'hide'
        ]();
    }

    function updateHTML() {
        $input.html.options({value: formatHTML()});
    }

    return that;

};