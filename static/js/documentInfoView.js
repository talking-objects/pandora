'use strict';

pandora.ui.documentInfoView = function(data) {

    var ui = pandora.user.ui,
        canEdit = pandora.site.capabilities.canEditMetadata[pandora.user.level] || data.editable,
        canRemove = pandora.site.capabilities.canRemoveItems[pandora.user.level],
        css = {
            marginTop: '4px',
            textAlign: 'justify'
        },
        html,
        iconRatio = data.ratio,
        iconSize = ui.infoIconSize,
        iconWidth = iconRatio > 1 ? iconSize : Math.round(iconSize * iconRatio),
        iconHeight = iconRatio < 1 ? iconSize : Math.round(iconSize / iconRatio),
        iconLeft = iconSize == 256 ? Math.floor((iconSize - iconWidth) / 2) : 0,
        borderRadius = ui.icons == 'posters' ? 0 : iconSize / 8,
        margin = 16,
        nameKeys = pandora.site.documentKeys.filter(function(key) {
            return key.sortType == 'person';
        }).map(function(key) {
            return key.id;
        }),
        listKeys = pandora.site.documentKeys.filter(function(key) {
            return Ox.isArray(key.type);
        }).map(function(key){
            return key.id;
        }),
        posterKeys = nameKeys.concat(['title', 'year']),
        statisticsWidth = 128,

        $bar = Ox.Bar({size: 16})
            .bindEvent({
                doubleclick: function(e) {
                    if ($(e.target).is('.OxBar')) {
                        $info.animate({scrollTop: 0}, 250);
                    }
                }
            }),

        $options = Ox.MenuButton({
                items: [
                    {
                        id: 'delete',
                        title: Ox._('Delete {0}...', [Ox._('Document')]),
                        disabled: !canRemove
                    }
                ],
                style: 'square',
                title: 'set',
                tooltip: Ox._('Options'),
                type: 'image',
            })
            .css({
                float: 'left',
                borderColor: 'rgba(0, 0, 0, 0)',
                background: 'rgba(0, 0, 0, 0)'
            })
            .bindEvent({
                click: function(data_) {
                    if (data_.id == 'delete') {
                        pandora.ui.deleteDocumentDialog(
                            [data],
                            function() {
                                Ox.Request.clearCache();
                                if (ui.document) {
                                    pandora.UI.set({document: ''});
                                } else {
                                    pandora.$ui.list.reloadList()
                                }
                            }
                        ).open();
                    }
                }
            })
            .appendTo($bar),

        $edit = Ox.MenuButton({
                items: [
                    {
                        id: 'insert',
                        title: Ox._('Insert HTML...'),
                        disabled: true
                    }
                ],
                style: 'square',
                title: 'edit',
                tooltip: Ox._('Edit'),
                type: 'image',
            })
            .css({
                float: 'right',
                borderColor: 'rgba(0, 0, 0, 0)',
                background: 'rgba(0, 0, 0, 0)'
            })
            .bindEvent({
                click: function(data) {
                    // ...
                }
            })
            .appendTo($bar),

        $info = Ox.Element().css({overflowY: 'auto'}),

        that = Ox.SplitPanel({
            elements: [
                {element: $bar, size: 16},
                {element: $info}
            ],
            orientation: 'vertical'
        }),

        $icon = Ox.Element({
                element: '<img>',
            })
            .attr({
                src: '/documents/' + data.id + '/512p.jpg?' + data.modified
            })
            .css({
                position: 'absolute',
                left: margin + iconLeft + 'px',
                top: margin + 'px',
                width: iconWidth + 'px',
                height: iconHeight + 'px',
                borderRadius: borderRadius + 'px',
                cursor: 'pointer'
            })
            .bindEvent({
                singleclick: open
            })
            .appendTo($info),

        $reflection = $('<div>')
            .addClass('OxReflection')
            .css({
                position: 'absolute',
                left: margin + 'px',
                top: margin + iconHeight + 'px',
                width: iconSize + 'px',
                height: iconSize / 2 + 'px',
                overflow: 'hidden'
            })
            .appendTo($info),

        $reflectionIcon = $('<img>')
            .attr({
                src: '/documents/' + data.id + '/512p.jpg?' + data.modified
            })
            .css({
                position: 'absolute',
                left: iconLeft + 'px',
                width: iconWidth + 'px',
                height: iconHeight + 'px',
                borderRadius: borderRadius + 'px'
            })
            .appendTo($reflection),

        $reflectionGradient = $('<div>')
            .css({
                position: 'absolute',
                width: iconSize + 'px',
                height: iconSize / 2 + 'px'
            })
            .appendTo($reflection),

        $text = Ox.Element()
            .addClass('OxTextPage')
            .css({
                position: 'absolute',
                left: margin + (iconSize == 256 ? 256 : iconWidth) + margin + 'px',
                top: margin + 'px',
                right: margin + statisticsWidth + margin + 'px',
            })
            .appendTo($info),

        $statistics = $('<div>')
            .css({
                position: 'absolute',
                width: statisticsWidth + 'px',
                top: margin + 'px',
                right: margin + 'px'
            })
            .appendTo($info),

        $capabilities;

    [$options, $edit].forEach(function($element) {
        $element.find('input').css({
            borderWidth: 0,
            borderRadius: 0,
            padding: '3px'
        });
    });

    listKeys.forEach(function(key) {
        if (Ox.isString(data[key])) {
            data[key] = [data[key]];
        }
    });

    if (!canEdit) {
        pandora.createLinks($info);
    }

    // Title -------------------------------------------------------------------

    $('<div>')
        .css({
            marginTop: '-2px',
        })
        .append(
            Ox.EditableContent({
                    editable: canEdit,
                    tooltip: canEdit ? pandora.getEditTooltip() : '',
                    value: data.title || ''
                })
                .css({
                    marginBottom: '-3px',
                    fontWeight: 'bold',
                    fontSize: '13px'
                })
                .bindEvent({
                    submit: function(event) {
                        editMetadata('title', event.value);
                    }
                })
        )
        .appendTo($text);

    // Director, Year and Country ----------------------------------------------

    renderGroup(['author', 'type', 'date']);
    renderGroup(['publisher', 'place', 'series', 'edition']);
    renderGroup(['language']);
    renderGroup(['extension', 'dimensions', 'size', 'user', 'matches']);


    // Description -----------------------------------------------------------------

    if (canEdit || data.description) {
        $('<div>')
            .append(
                Ox.EditableContent({
                    clickLink: pandora.clickLink,
                    editable: canEdit,
                    format: function(value) {
                        return value.replace(
                            /<img src=/g,
                            '<img style="float: left; max-width: 256px; max-height: 256px; margin: 0 16px 16px 0" src='
                        );
                    },
                    maxHeight: Infinity,
                    placeholder: formatLight(Ox._('No Description')),
                    tooltip: canEdit ? pandora.getEditTooltip() : '',
                    type: 'textarea',
                    value: data.description || ''
                })
                .css(css)
                .css({
                    marginTop: '12px',
                    overflow: 'hidden'
                })
                .bindEvent({
                    submit: function(event) {
                        editMetadata('description', event.value);
                    }
                })
            )
            .appendTo($text);
    }

    // Created and Modified ----------------------------------------------------

    ['created', 'modified'].forEach(function(key) {
        $('<div>')
            .css({marginBottom: '4px'})
            .append(formatKey(key, 'statistics'))
            .append(
                $('<div>').html(Ox.formatDate(data[key], '%B %e, %Y'))
            )
            .appendTo($statistics);
    });
    /*
    $('<div>')
        .css({marginBottom: '4px'})
        .append(formatKey('timesaccessed', 'statistics'))
        .append(
            $('<div>').html(data.timesaccessed)
        )
        .appendTo($statistics);
    */

    // Rights Level ------------------------------------------------------------

    var $rightsLevel = $('<div>');
    $('<div>')
        .css({marginBottom: '4px'})
        .append(formatKey('Rights Level', 'statistics'))
        .append($rightsLevel)
        .appendTo($statistics);
    renderRightsLevel();

    function editMetadata(key, value) {
        if (value != data[key]) {
            var edit = {id: data.id};
            if (key == 'title') {
                edit[key] = value;
            } else if (listKeys.indexOf(key) >= 0) {
                edit[key] = value ? value.split(', ') : [];
            } else {
                edit[key] = value ? value : null;
            }
            pandora.api.editDocument(edit, function(result) {
                var src;
                data[key] = result.data[key];
                Ox.Request.clearCache(); // fixme: too much? can change filter/list etc
                if (result.data.id != data.id) {
                    pandora.UI.set({document: result.data.id});
                    pandora.$ui.browser.value(data.id, 'id', result.data.id);
                }
                //pandora.updateItemContext();
                //pandora.$ui.browser.value(result.data.id, key, result.data[key]);
                pandora.$ui.itemTitle
                    .options({title: '<b>' + (pandora.getDocumentTitle(result.data)) + '</b>'});
            });
        }
    }

    function formatKey(key, mode) {
        var item = Ox.getObjectById(pandora.site.itemKeys, key);
        key = Ox._(item ? item.title : key);
        mode = mode || 'text';
        return mode == 'text'
            ? '<span style="font-weight: bold">' + Ox.toTitleCase(key) + ':</span> '
            : mode == 'description'
            ? Ox.toTitleCase(key)
            : Ox.Element()
                .css({marginBottom: '4px', fontWeight: 'bold'})
                .html(Ox.toTitleCase(key)
                .replace(' Per ', ' per '));
    }

    function formatLight(str) {
        return '<span class="OxLight">' + str + '</span>';
    }

    function formatLink(value, key) {
        return (Ox.isArray(value) ? value : [value]).map(function(value) {
            return key
                ? '<a href="/documents/' + key + '=' + value + '">' + value + '</a>'
                : value;
        }).join(', ');
    }

    function formatValue(key, value) {
        var ret;
        if (key == 'date') {
            ret = value ? Ox.formatDate(value,
                ['', '%Y', '%B %Y', '%B %e, %Y'][value.split('-').length],
                true
            ) : '';
        } else if (nameKeys.indexOf(key) > -1) {
            ret = formatLink(value.split(', '), key);
        } else if (listKeys.indexOf(key) > -1) {
            ret = formatLink(value.split(', '), key);
        } else if (['type'].indexOf(key) > -1) {
            ret = formatLink(value, key);
        } else {
            ret = pandora.formatDocumentKey(Ox.getObjectById(pandora.site.documentKeys, key), data);
        }
        return ret;
    }

    function getRightsLevelElement(rightsLevel) {
        return Ox.Theme.formatColorLevel(
            rightsLevel,
            pandora.site.documentRightsLevels.map(function(rightsLevel) {
                return rightsLevel.name;
            })
        );
    }

    function getValue(key, value) {
        return !value ? ''
            : Ox.contains(listKeys, key) ? value.join(', ')
            : value;
    }

    function renderCapabilities(rightsLevel) {
        var capabilities = [].concat(
                canEdit ? [{name: 'canSeeItem', symbol: 'Find'}] : [],
                [
                    {name: 'canPlayClips', symbol: 'PlayInToOut'},
                    {name: 'canPlayVideo', symbol: 'Play'},
                    {name: 'canDownloadVideo', symbol: 'Download'}
                ]
            ),
            userLevels = canEdit ? pandora.site.userLevels : [pandora.user.level];
        $capabilities.empty();
        userLevels.forEach(function(userLevel, i) {
            var $element,
                $line = $('<div>')
                    .css({
                        height: '16px',
                        marginBottom: '4px'
                    })
                    .appendTo($capabilities);
            if (canEdit) {
                $element = Ox.Theme.formatColorLevel(i, userLevels.map(function(userLevel) {
                    return Ox.toTitleCase(userLevel);
                }), [0, 240]);
                Ox.Label({
                        textAlign: 'center',
                        title: Ox.toTitleCase(userLevel),
                        width: 60
                    })
                    .addClass('OxColor OxColorGradient')
                    .css({
                        float: 'left',
                        height: '12px',
                        paddingTop: '2px',
                        background: $element.css('background'),
                        fontSize: '8px',
                        color: $element.css('color')
                    })
                    .data({OxColor: $element.data('OxColor')})
                    .appendTo($line);
            }
            capabilities.forEach(function(capability) {
                var hasCapability = pandora.site.capabilities[capability.name][userLevel] >= rightsLevel,
                    $element = Ox.Theme.formatColorLevel(hasCapability, ['', '']);
                Ox.Button({
                        tooltip: (canEdit ? Ox.toTitleCase(userLevel) : 'You') + ' '
                            + (hasCapability ? 'can' : 'can\'t') + ' '
                            + Ox.toSlashes(capability.name)
                                .split('/').slice(1).join(' ')
                                .toLowerCase(),
                        title: capability.symbol,
                        type: 'image'
                    })
                    .addClass('OxColor OxColorGradient')
                    .css({background: $element.css('background')})
                    .css('margin' + (canEdit ? 'Left' : 'Right'), '4px')
                    .data({OxColor: $element.data('OxColor')})
                    .appendTo($line);
            });
            if (!canEdit) {
                Ox.Button({
                    title: Ox._('Help'),
                    tooltip: Ox._('About Rights'),
                    type: 'image'
                })
                .css({marginLeft: '52px'})
                .bindEvent({
                    click: function() {
                        pandora.UI.set({page: 'rights'});
                    }
                })
                .appendTo($line);
            }
        });
    }

    function renderGroup(keys) {
        var $element;
        if (canEdit || keys.filter(function(key) {
            return data[key];
        }).length) {
            $element = $('<div>').addClass('OxSelectable').css(css);
            keys.forEach(function(key, i) {
                if (canEdit || data[key]) {
                    if ($element.children().length) {
                        $('<span>').html('; ').appendTo($element);
                    }
                    $('<span>').html(formatKey(key)).appendTo($element);
                    Ox.EditableContent({
                            clickLink: pandora.clickLink,
                            format: function(value) {
                                return formatValue(key, value);
                            },
                            placeholder: formatLight(Ox._('unknown')),
                            tooltip: canEdit ? pandora.getEditTooltip() : '',
                            value: getValue(key, data[key])
                        })
                        .bindEvent({
                            submit: function(data) {
                                editMetadata(key, data.value);
                            }
                        })
                        .appendTo($element);
                }
            });
            $element.appendTo($text);
        }
    }

    function renderRightsLevel() {
        var $rightsLevelElement = getRightsLevelElement(data.rightslevel),
            $rightsLevelSelect;
        $rightsLevel.empty();
        if (canEdit) {
            $rightsLevelSelect = Ox.Select({
                    items: pandora.site.documentRightsLevels.map(function(rightsLevel, i) {
                        return {id: i, title: rightsLevel.name};
                    }),
                    width: 128,
                    value: data.rightslevel
                })
                .addClass('OxColor OxColorGradient')
                .css({
                    marginBottom: '4px',
                    background: $rightsLevelElement.css('background')
                })
                .data({OxColor: $rightsLevelElement.data('OxColor')})
                .bindEvent({
                    change: function(event) {
                        var rightsLevel = event.value;
                        $rightsLevelElement = getRightsLevelElement(rightsLevel);
                        $rightsLevelSelect
                            .css({background: $rightsLevelElement.css('background')})
                            .data({OxColor: $rightsLevelElement.data('OxColor')})
                        //renderCapabilities(rightsLevel);
                        pandora.api.editDocument({id: data.id, rightslevel: rightsLevel}, function(result) {
                            // ...
                        });
                    }
                })
                .appendTo($rightsLevel);
        } else {
            $rightsLevelElement
                .css({
                    marginBottom: '4px'
                })
                .appendTo($rightsLevel);
        }
        $capabilities = $('<div>').appendTo($rightsLevel);
        //renderCapabilities(data.rightslevel);
    }

    function open() {
        pandora.UI.set({
            documentView: 'view',
        });
    }

    that.reload = function() {
        var src = '/documents/' + data.id + '/512p.jpg?' + data.modified;
        $icon.attr({src: src});
        $reflectionIcon.attr({src: src});
        iconSize = iconSize == 256 ? 512 : 256;
        iconRatio = ui.icons == 'posters'
            ? (ui.showSitePosters ? pandora.site.posters.ratio : data.posterRatio) : 1;
        toggleIconSize();
    };

    that.bindEvent({
        mousedown: function() {
            setTimeout(function() {
                !Ox.Focus.focusedElementIsInput() && that.gainFocus();
            });
        },
        pandora_icons: that.reload,
        pandora_showsiteposters: function() {
            ui.icons == 'posters' && that.reload();
        }
    });

    return that;

};
