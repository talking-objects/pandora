'use strict';

pandora.ui.infoView = function(data, isMixed) {
    isMixed = isMixed || {};

    var ui = pandora.user.ui,
        isMultiple = arguments.length == 2,
        canEdit = pandora.hasCapability('canEditMetadata') || isMultiple || data.editable,
        canRemove = pandora.hasCapability('canRemoveItems') || data.editable,
        css = {
            marginTop: '4px',
            textAlign: 'justify'
        },
        descriptions = [],
        html,
        iconRatio = ui.icons == 'posters' ? data.posterRatio : 1,
        iconSize = isMultiple ? 0 : ui.infoIconSize,
        iconWidth = isMultiple ? 0 : iconRatio > 1 ? iconSize : Math.round(iconSize * iconRatio),
        iconHeight = iconRatio < 1 ? iconSize : Math.round(iconSize / iconRatio),
        iconLeft = iconSize == 256 ? Math.floor((iconSize - iconWidth) / 2) : 0,
        borderRadius = ui.icons == 'posters' ? 0 : iconSize / 8,
        margin = 16,
        nameKeys = pandora.site.itemKeys.filter(function(key) {
            return key.sortType == 'person';
        }).map(function(key) {
            return key.id;
        }),
        listKeys = pandora.site.itemKeys.filter(function(key) {
            return Ox.isArray(key.type);
        }).map(function(key){
            return key.id;
        }),
        posterKeys = ['title', 'date'],
        displayedKeys = [ // FIXME: can tis be a flag in the config?
            'title', 'notes', 'name', 'summary', 'id',
            'hue', 'saturation', 'lightness', 'cutsperminute', 'volume',
            'user', 'rightslevel', 'bitrate', 'timesaccessed',
            'numberoffiles', 'numberofannotations', 'numberofcuts', 'words', 'wordsperminute',
            'annotations', 'groups', 'filename',
            'duration', 'aspectratio', 'pixels', 'size', 'resolution',
            'created', 'modified', 'accessed',
            'random'
        ],
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
                        id: 'toggle',
                        title: Ox._('Toggle {0} size...', [
                            Ox._(ui.icons == 'posters' ? 'poster' : 'icon')
                        ]),
                    },
                    {
                        id: 'delete',
                        title: Ox._('Delete {0}...', [pandora.site.itemName.singular]),
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
                    if (data_.id == 'toggle') {
                        toggleIconSize()
                    } else if (data_.id == 'delete') {
                        pandora.$ui.deleteItemsDialog = pandora.ui.deleteItemsDialog({
                            items: [data]
                        }).open();
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
                {element: $bar, size: isMultiple ? 0 : 16},
                {element: $info}
            ],
            orientation: 'vertical'
        }),

        $left = Ox.Element()
            .css({
                position: 'absolute'
            })
            .appendTo($info);

        if (!isMultiple) {
            var $icon = Ox.Element({
                    element: '<img>',
                    tooltip: 'Switch to ' + Ox.getObjectById(
                        pandora.site.itemViews,
                        ui.videoView
                    ).title + ' View'
                })
                .attr({
                    src: pandora.getMediaURL('/' + data.id + '/' + (
                        ui.icons == 'posters' ? 'poster' : 'icon'
                    ) + '512.jpg?' + data.modified)
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
                    anyclick: function() {
                        pandora.UI.set({itemView: ui.videoView});
                    }
                })
                .appendTo($left),

            $reflection = $('<div>')
                .addClass('OxReflection')
                .css({
                    position: 'absolute',
                    left: margin + 'px',
                    top: margin + iconHeight + 'px',
                    width: iconSize + 'px',
                    height: Math.round(iconSize / 2) + 'px',
                    overflow: 'hidden'
                })
                .appendTo($left),

            $reflectionIcon = $('<img>')
                .attr({
                    src: pandora.getMediaURL('/' + data.id + '/' + (
                        ui.icons == 'posters' ? 'poster' : 'icon'
                    ) + '512.jpg?' + data.modified)
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
                    height: Math.round(iconSize / 2) + 'px'
                })
                .appendTo($reflection);
        }

        var $data = $('<div>')
            .addClass('OxTextPage')
            .css({
                position: 'absolute',
                left: margin + 'px',
                top: margin + iconHeight + margin + 'px',
                width: iconSize + 'px',
            })
            .appendTo($left),

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
            .appendTo($info);

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

    // Source & Project --------------------------------------------------------
    if (!isMultiple) {

    ['source', 'project'].forEach(function(key) {
        displayedKeys.push(key);
        if (canEdit || data[key]) {
            var $div = $('<div>')
                .addClass('OxSelectable')
                .css(css)
                .css({margin: 0})
                .appendTo($data);
            $('<span>')
                .html(
                    formatKey({
                        category: 'categories',
                    }[key] || key).replace('</span>', '&nbsp;</span>')
                )
                .appendTo($div);
            Ox.EditableContent({
                    clickLink: pandora.clickLink,
                    format: function(value) {
                        return formatValue(key, value);
                    },
                    placeholder: formatLight(Ox._(isMixed[key] ? 'mixed' : 'unknown')),
                    editable: canEdit,
                    tooltip: canEdit ? pandora.getEditTooltip() : '',
                    value: listKeys.indexOf(key) >= 0
                          ? (data[key] || []).join(', ')
                          : data[key] || ''
                })
                .bindEvent({
                    submit: function(event) {
                        editMetadata(key, event.value);
                    }
                })
                .appendTo($div);
            if (canEdit || data[key + 'description']) {
                $('<div>')
                    .addClass("InlineImages")
                    .append(
                        descriptions[key] = Ox.EditableContent({
                            clickLink: pandora.clickLink,
                            editable: canEdit,
                            placeholder: formatLight(Ox._('No {0} Description', [Ox._(Ox.toTitleCase(key))])),
                            tooltip: canEdit ? pandora.getEditTooltip() : '',
                            type: 'textarea',
                            value: data[key + 'description'] || ''
                        })
                        .css(css)
                        .bindEvent({
                            submit: function(event) {
                                editMetadata(key + 'description', event.value);
                            }
                        })
                    ).css({
                        margin: '12px 0',
                    })
                    .appendTo($div);
            }
        }
    });
    }

    // Title -------------------------------------------------------------------
    if (!isMultiple) {

    $('<div>')
        .css({
            marginTop: '-2px',
            marginBottom: '12px'
        })
        .append(
            Ox.EditableContent({
                    editable: canEdit,
                    placeholder: formatLight(Ox._('No Title')),
                    tooltip: canEdit ? pandora.getEditTooltip() : '',
                    value: data.title || ""
                })
                .css({
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
    }

    // Groups ------------------------------------------------------------------

    renderGroup(['location', 'date', 'language']);

    renderGroup(['director', 'cinematographer', 'featuring']);
    if (isMultiple) {
        renderGroup(['source', 'project']);
    }

    renderGroup(['topic']);

    // Summary -------------------------------------------------------------

    if (canEdit || data.summary) {
        $('<div>')
            .addClass("InlineImages")
            .css({
                marginTop: '12px',
                marginBottom: '12px'
            })
            .append(
                Ox.EditableContent({
                    clickLink: pandora.clickLink,
                    collapseToEnd: false,
                    editable: canEdit,
                    maxHeight: Infinity,
                    placeholder: formatLight(Ox._('No Summary')),
                    tooltip: canEdit ? pandora.getEditTooltip() : '',
                    type: 'textarea',
                    value: data.summary || ''
                })
                .css(css)
                .css({
                    overflow: 'hidden'
                })
                .bindEvent({
                    submit: function(event) {
                        editMetadata('summary', event.value);
                    }
                })
            )
            .appendTo($text);
        $('<div>').css({width: '1px', height: 0, clear: 'both'}).appendTo($text);
    }

    // License -----------------------------------------------------------------

    Ox.getObjectById(pandora.site.itemKeys, 'license') && renderGroup(['license']);


    $('<div>')
        .addClass('OxSelectable')
        .css(css)
        .css({height: '16px'})
        .appendTo($text);

    // Render any remaing keys defined in config

    renderRemainingKeys();


    // Duration, Aspect Ratio --------------------------------------------------
    if (!isMultiple) {
    ['duration', 'aspectratio'].forEach(function(key) {
        var itemKey = Ox.getObjectById(pandora.site.itemKeys, key),
            value = data[key] || 0;
        $('<div>')
            .css({marginBottom: '4px'})
            .append(formatKey(itemKey.title, 'statistics'))
            .append(
                Ox.Theme.formatColor(null, 'gradient')
                    .css({textAlign: 'right'})
                    .html(
                        Ox['format' + Ox.toTitleCase(itemKey.format.type)]
                            .apply(null, [value].concat(itemKey.format.args))
                    )
            )
            .appendTo($statistics);
    });

    // Hue, Saturation, Lightness, Volume --------------------------------------

    ['hue', 'saturation', 'lightness', 'volume'].forEach(function(key) {
        $('<div>')
            .css({marginBottom: '4px'})
            .append(formatKey(key, 'statistics'))
            .append(
                Ox.Theme.formatColor(
                    data[key] || 0, key == 'volume' ? 'lightness' : key
                ).css({textAlign: 'right'})
            )
            .appendTo($statistics);
    });

    // Cuts per Minute ---------------------------------------------------------

    $('<div>')
        .css({marginBottom: '4px'})
        .append(formatKey('cuts per minute', 'statistics'))
        .append(
            Ox.Theme.formatColor(null, 'gradient')
                .css({textAlign: 'right'})
                .html(Ox.formatNumber(data['cutsperminute'] || 0, 3))
        )
        .appendTo($statistics);
    }
    // Rights Level ------------------------------------------------------------

    var $rightsLevel = $('<div>');
    $('<div>')
        .css({marginBottom: '4px'})
        .append(formatKey(Ox._('Rights Level'), 'statistics'))
        .append($rightsLevel)
        .appendTo($statistics);
    pandora.renderRightsLevel(that, $rightsLevel, data, isMixed, isMultiple, canEdit);

    // User and Groups ---------------------------------------------------------
    if (!isMultiple || pandora.hasCapability('canEditUsers')) {

    ['user', 'groups'].forEach(function(key) {
        if (key == 'groups' && isMultiple) {
            return
        };
        var $input;
        (canEdit || data[key] && data[key].length) && $('<div>')
            .css({marginBottom: '4px'})
            .append(formatKey(key, 'statistics'))
            .append(
                $('<div>')
                    .css({margin: '2px 0 0 -1px'}) // fixme: weird
                    .append(
                        $input = Ox.Editable({
                            placeholder: key == 'groups'
                                ? formatLight(Ox._(isMixed[key] ? 'Mixed Groups' : 'No Groups'))
                                : isMixed[key] ? formatLight(Ox._('Mixed Users')) : '',
                            editable: key == 'user' && canEdit,
                            tooltip: canEdit ? pandora.getEditTooltip() : '',
                            value: isMixed[key]
                                ? ''
                                : key == 'user' ? data[key] : data[key].join(', ')
                        })
                        .bindEvent(Ox.extend({
                            submit: function(event) {
                                editMetadata(key, event.value);
                            }
                        }, key == 'groups' ? {
                            doubleclick: canEdit ? function() {
                                setTimeout(function() {
                                    if (window.getSelection) {
                                        window.getSelection().removeAllRanges();
                                    } else if (document.selection) {
                                        document.selection.empty();
                                    }
                                });
                                pandora.$ui.groupsDialog = pandora.ui.groupsDialog({
                                        id: data.id,
                                        name: data.title,
                                        type: 'item'
                                    })
                                    .bindEvent({
                                        groups: function(data) {
                                            $input.options({
                                                value: data.groups.join(', ')
                                            });
                                        }
                                    })
                                    .open();
                            } : function() {}
                        } : {}))
                    )
            )
            .appendTo($statistics);
    });

    }
    // Created and Modified ----------------------------------------------------
    if (!isMultiple) {

    ['created', 'modified'].forEach(function(key) {
        $('<div>')
            .css({marginBottom: '4px'})
            .append(formatKey(key, 'statistics'))
            .append(
                $('<div>').html(Ox.formatDate(data[key], '%B %e, %Y'))
            )
            .appendTo($statistics);
    });

    }

    // Notes --------------------------------------------------------------------

    if (canEdit) {
        $('<div>')
            .css({marginBottom: '4px'})
            .append(
                formatKey('Notes', 'statistics').options({
                    tooltip: Ox._('Only {0} can see and edit these comments', [
                        Object.keys(pandora.site.capabilities.canEditMetadata).map(function(level, i) {
                            return (
                                i == 0 ? ''
                                : i < Ox.len(pandora.site.capabilities.canEditMetadata) - 1 ? ', '
                                : ' ' + Ox._('and') + ' '
                            ) + Ox.toTitleCase(level)
                        }).join('')])
                })
            )
            .append(
                Ox.EditableContent({
                        height: 128,
                        placeholder: formatLight(Ox._('No notes')),
                        tooltip: pandora.getEditTooltip(),
                        type: 'textarea',
                        value: data.notes || '',
                        width: 128
                    })
                    .bindEvent({
                        submit: function(event) {
                            editMetadata('notes', event.value);
                        }
                    })
            )
            .appendTo($statistics);
    }

    $('<div>').css({height: '16px'}).appendTo($statistics);

    function editMetadata(key, value) {
        if (value != data[key]) {
            var edit = {id: isMultiple ? ui.listSelection : data.id};
            if (key == 'title') {
                edit[key] = value;
            } else if (listKeys.indexOf(key) >= 0) {
                edit[key] = value ? value.split(', ') : [];
            } else {
                edit[key] = value ? value : null;
            }
            pandora.api.edit(edit, function(result) {
                Ox.Request.clearCache(); // fixme: too much? can change filter/list etc
                if (!isMultiple) {
                    var src;
                    data[key] = result.data[key];
                    descriptions[key] && descriptions[key].options({
                        value: result.data[key + 'description']
                    });
                    if (result.data.id != data.id) {
                        pandora.UI.set({item: result.data.id});
                        pandora.$ui.browser.value(data.id, 'id', result.data.id);
                    }
                    pandora.updateItemContext();
                    pandora.$ui.browser.value(result.data.id, key, result.data[key]);
                    if (Ox.contains(posterKeys, key) && ui.icons == 'posters') {
                        src = pandora.getMediaURL('/' + data.id + '/poster512.jpg?' + Ox.uid());
                        $icon.attr({src: src});
                        $reflectionIcon.attr({src: src});
                    }
                    pandora.$ui.itemTitle
                        .options({
                            title: '<b>' + result.data.title
                                + (Ox.len(result.data.director)
                                    ? ' (' + result.data.director.join(', ') + ')'
                                    : '')
                                + (result.data.year ? ' ' + result.data.year : '') + '</b>'
                        });
                    //pandora.$ui.contentPanel.replaceElement(0, pandora.$ui.browser = pandora.ui.browser());
                }
                that.triggerEvent('change', Ox.extend({}, key, value));
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

    function formatLink(key, value, linkValue) {
        return (Ox.isArray(value) ? value : [value]).map(function(value) {
            return key
                ? '<a href="/' + key + '=' + pandora.escapeQueryValue(
                    Ox.decodeHTMLEntities(linkValue ? linkValue : value)
                ) + '">' + value + '</a>'
                : value;
        }).join(', ');
    }

    function formatValue(key, value) {
        var ret;
        if (key == 'date' && (!value || value.split('-').length < 4)) {
            ret = pandora.formatDate(value);
        } else if (listKeys.indexOf(key) > -1) {
            ret = value.split(', ');
        } else {
            ret = value;
        }
        if (nameKeys.indexOf(key) > -1) {
            key = 'name';
        }
        return formatLink(key, ret, key == 'date' && value);
    }

    function getValue(key, value) {
        return !value ? ''
            : Ox.contains(listKeys, key) ? value.join(', ')
            : value;
    }

    function renderGroup(keys) {
        var $element;
        keys.forEach(function(key) { displayedKeys.push(key) });
        if (canEdit || keys.filter(function(key) {
            return data[key];
        }).length) {
            $element = $('<div>')
                .addClass('OxSelectable')
                .css(css);
            keys.forEach(function(key, i) {
                if (canEdit || data[key]) {
                    if ($element.children().length) {
                        $('<span>').html('; ').appendTo($element);
                    }
                    $('<span>').html(formatKey(key)).appendTo($element);
                    Ox.EditableContent({
                            clickLink: pandora.clickLink,
                            editable: canEdit,
                            format: function(value) {
                                return formatValue(key, value);
                            },
                            placeholder: formatLight(Ox._(isMixed[key] ? 'mixed' : 'unknown')),
                            tooltip: canEdit ? pandora.getEditTooltip() : '',
                            value: getValue(key, data[key])
                        })
                        .bindEvent({
                            submit: function(data) {
                                editMetadata(key, data.value);
                            }
                        })
                        .appendTo($element);
                    if (isMixed[key] && Ox.contains(listKeys, key)) {
                        pandora.ui.addRemoveKeyDialog({
                            ids: ui.listSelection,
                            key: key,
                            section: ui.section
                        }).appendTo($element)
                    }
                }
            });
            $element.appendTo($text);
        }
        return $element;
    }

    function renderRemainingKeys() {
        var keys = pandora.site.itemKeys.filter(function(item) {
            return item.id != '*' && item.type != 'layer' && !Ox.contains(displayedKeys, item.id);
        }).map(function(item) {
            return item.id;
        });
        if (keys.length) {
            renderGroup(keys)
        }
    }


    function toggleIconSize() {
        iconSize = iconSize == 256 ? 512 : 256;
        iconWidth = iconRatio > 1 ? iconSize : Math.round(iconSize * iconRatio);
        iconHeight = iconRatio < 1 ? iconSize : Math.round(iconSize / iconRatio);
        iconLeft = iconSize == 256 ? Math.floor((iconSize - iconWidth) / 2) : 0,
        borderRadius = ui.icons == 'posters' ? 0 : iconSize / 8;
        $icon.animate({
            left: margin + iconLeft + 'px',
            width: iconWidth + 'px',
            height: iconHeight + 'px',
            borderRadius: borderRadius + 'px'
        }, 250);
        $reflection.animate({
            top: margin + iconHeight + 'px',
            width: iconSize + 'px',
            height: iconSize / 2 + 'px'
        }, 250);
        $reflectionIcon.animate({
            left: iconLeft + 'px',
            width: iconWidth + 'px',
            height: iconHeight + 'px',
            borderRadius: borderRadius + 'px'
        }, 250);
        $reflectionGradient.animate({
            width: iconSize + 'px',
            height: iconSize / 2 + 'px'
        }, 250);
        $data.animate({
            top: margin + iconHeight + margin + 'px',
            width: iconSize + 'px',
        }, 250);
        $text.animate({
            left: margin + (iconSize == 256 ? 256 : iconWidth) + margin + 'px',
        }, 250);
        pandora.UI.set({infoIconSize: iconSize});
    }

    that.reload = function() {
        var src = pandora.getMediaURL('/' + data.id + '/' + (
            ui.icons == 'posters' ? 'poster' : 'icon'
        ) + '512.jpg?' + Ox.uid());
        $icon.attr({src: src});
        $reflectionIcon.attr({src: src});
        iconSize = iconSize == 256 ? 512 : 256;
        iconRatio = ui.icons == 'posters'
            ? (ui.showSitePosters ? pandora.site.posters.ratio : data.posterRatio) : 1;
        toggleIconSize();
    };

    that.resizeElement = function() {
        // overwrite splitpanel resize
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
