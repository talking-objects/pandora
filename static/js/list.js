'use strict';

pandora.ui.list = function() {

    var that,
        ui = pandora.user.ui,
        view = ui.listView;

    if (view == 'list') {
        that = Ox.TableList({
            columns: [].concat([{
                align: 'center',
                defaultWidth: 16,
                format: function(value, data) {
                    var icon, width, height, margin, marginCSS, borderRadius;
                    if (ui.icons == 'posters') {
                        icon = 'poster';
                        width = value < 1 ? Math.round(14 * value / 2) * 2 : 14;
                        height = value < 1 ? 14 : Math.round(14 / value / 2) * 2;
                        margin = value < 1 ? Math.floor(7 - width / 2) - 3 : Math.floor(7 - height / 2);
                        marginCSS = value < 1 ? '0 0 0 ' + margin + 'px' : margin + 'px 0 0 -3px';
                        borderRadius = 0;
                    } else {
                        icon = 'icon';
                        width = 14;
                        height = 14;
                        marginCSS = '0 0 0 -3px';
                        borderRadius = '3px';
                    }
                    return $('<img>').css({
                        width: width - 2 + 'px',
                        height: height - 2 + 'px',
                        border: '1px solid rgb(48, 48, 48)',
                        borderRadius: '2px',
                        margin: marginCSS,
                        background: '-webkit-linear-gradient(top, rgb(32, 32, 32), rgb(0, 0, 0))'
                    }).load(function() {
                        $(this).css({
                            width: width + 'px',
                            height: height + 'px',
                            border: 0,
                            borderRadius: borderRadius
                            //background: 'transparent'
                        });
                    }).attr({
                        src: pandora.getMediaURL('/' + data.id + '/' + icon + '14.jpg?' + data.modified)
                    });
                },
                id: 'posterRatio',
                resizable: false,
                title: Ox._('Icon'),
                titleImage: ui.icons == 'posters' ? 'SetPoster' : 'Icon',
                visible: ui.listColumns.indexOf('posterRatio') > -1,
                width: 16
            }], pandora.site.sortKeys.filter(function(key) {
                return !key.capability
                    || pandora.hasCapability(key.capability);
            }).map(function(key) {
                var position = ui.listColumns.indexOf(key.id);
                return {
                    addable: key.id != 'random',
                    align: ['string', 'text'].indexOf(
                        Ox.isArray(key.type) ? key.type[0]: key.type
                    ) > -1 ? 'left' : key.type == 'list' ? 'center' : 'right',
                    defaultWidth: key.columnWidth,
                    format: key.format,
                    id: key.id,
                    operator: pandora.getSortOperator(key.id),
                    position: position,
                    removable: !key.columnRequired,
                    title: Ox._(key.title),
                    type: key.type,
                    visible: position > -1,
                    width: ui.listColumnWidth[key.id] || key.columnWidth
                };
            })),
            columnsMovable: true,
            columnsRemovable: true,
            columnsResizable: true,
            columnsVisible: true,
            draggable: true,
            id: 'list',
            items: function(data, callback) {
                //Ox.Log('', 'data, pandora.Query.toObject', data, pandora.Query.toObject())
                pandora.api.find(Ox.extend(data, {
                    query: ui.find,
                    keys: data.keys ? ['editable', 'modified'].concat(data.keys) : void 0
                }), callback);
                return Ox.clone(data, true);
            },
            scrollbarVisible: true,
            selected: ui.listSelection,
            sort: ui.listSort,
            unique: 'id'
        })
        .bindEvent({
            columnchange: function(data) {
                var columnWidth = {};
                pandora.UI.set({listColumns: data.ids});
                /*
                data.ids.forEach(function(id) {
                    columnWidth[id] =
                        ui.lists[ui.list].columnWidth[id]
                        || Ox.getObjectById(pandora.site.sortKeys, id).width
                });
                pandora.UI.set({listColumnWidth: columnWidth});
                */
            },
            columnresize: function(data) {
                pandora.UI.set('listColumnWidth.' + data.id, data.width);
            },
            sort: function(data) {
                pandora.UI.set({
                    listSort: [{key: data.key, operator: data.operator}]
                });
            }
        });
    } else if (view == 'grid') {
        that = Ox.IconList({
            borderRadius: ui.icons == 'posters' ? 0 : 16,
            defaultRatio: ui.icons == 'posters' ? pandora.site.posters.ratio : 1,
            draggable: true,
            id: 'list',
            item: function(data, sort, size) {
                var ratio = ui.icons == 'posters'
                        ? (ui.showSitePosters ? pandora.site.posters.ratio : data.posterRatio) : 1,
                    url = pandora.getMediaURL('/' + data.id + '/' + (
                        ui.icons == 'posters'
                        ? (ui.showSitePosters ? 'siteposter' : 'poster') : 'icon'
                    ) + size + '.jpg?' + data.modified),
                    format, info, sortKey = sort[0].key;
                if (['title', 'director', 'random'].indexOf(sortKey) > -1) {
                    info = data['year'] || data['date'] || '';
                } else {
                    format = pandora.getSortKeyData(sortKey).format;
                    if (Ox.isUndefined(data[sortKey]) || Ox.isNull(data[sortKey])) {
                        info = '';
                    } else if (format) {
                        info = (
                            /^color/.test(format.type.toLowerCase()) ? Ox.Theme : Ox
                        )['format' + Ox.toTitleCase(format.type)].apply(
                            this, [data[sortKey]].concat(format.args || [])
                        );
                        if (sortKey == 'rightslevel') {
                            info.css({width: size * 0.75 + 'px'});
                        }
                    } else {
                        info = data[sortKey] || '';
                    }
                }
                size = size || 128;
                return {
                    height: Math.round(ratio <= 1 ? size : size / ratio),
                    id: data.id,
                    info: info,
                    title: pandora.getItemTitle(data),
                    url: url,
                    width: Math.round(ratio >= 1 ? size : size * ratio)
                };
            },
            items: function(data, callback) {
                pandora.api.find(Ox.extend(data, {
                    query: ui.find
                }), callback);
                return Ox.clone(data, true);
            },
            keys: ['id', 'editable', 'modified', 'posterRatio'].concat(pandora.site.itemTitleKeys),
            selected: ui.listSelection,
            size: 128,
            sort: ui.listSort,
            unique: 'id'
        })
        .addClass('OxMedia');
    } else if (view == 'info') {
        that = Ox.Element().css({margin: '16px'}).html(view + ' results view still missing.');
    } else if (view == 'clips') {
        that = Ox.InfoList({
            borderRadius: ui.icons == 'posters' ? 0 : 16,
            defaultRatio: ui.icons == 'posters' ? pandora.site.posters.ratio : 1,
            draggable: true,
            id: 'list',
            item: function(data, sort, size) {
                size = 128;
                data.videoRatio = data.videoRatio || pandora.site.video.previewRatio;
                var ratio = ui.icons == 'posters'
                        ? (ui.showSitePosters ? pandora.site.posters.ratio : data.posterRatio) : 1,
                    url = pandora.getMediaURL('/' + data.id + '/' + (
                        ui.icons == 'posters'
                        ? (ui.showSitePosters ? 'siteposter' : 'poster') : 'icon'
                    ) + size + '.jpg?' + data.modified),
                    format, info, sortKey = sort[0].key;
                if (['title', 'director'].indexOf(sortKey) > -1) {
                    info = data['year'] || data['date'] || '';
                } else {
                    format = pandora.getSortKeyData(sortKey).format;
                    if (Ox.isUndefined(data[sortKey]) || Ox.isNull(data[sortKey])) {
                        info = '';
                    } else if (format) {
                        info = (
                            /^color/.test(format.type.toLowerCase()) ? Ox.Theme : Ox
                        )['format' + Ox.toTitleCase(format.type)].apply(
                            this, [data[sortKey]].concat(format.args || [])
                        );
                        if (sortKey == 'rightslevel') {
                            info.css({width: size * 0.75 + 'px'});
                        }
                    } else {
                        info = data[sortKey] || '';
                    }
                }
                return {
                    icon: {
                        height: Math.round(ratio <= 1 ? size : size / ratio),
                        id: data.id,
                        info: info,
                        title: pandora.getItemTitle(data),
                        url: url,
                        width: Math.round(ratio >= 1 ? size : size * ratio)
                    },
                    info: {
                        css: {marginTop: '2px'},
                        element: pandora.ui.itemClips,
                        id: data.id,
                        options: {
                            clips: data.clips,
                            duration: data.duration,
                            id: data.id,
                            ratio: data.videoRatio
                        }
                    }
                };
            },
            items: function(data, callback) {
                pandora.getClipsQuery(function(clipsQuery) {
                    pandora.api.find(Ox.extend(data, {
                        query: ui.find,
                        clips: {
                            query: clipsQuery,
                            items: pandora.getClipsItems(),
                            keys: []
                        }
                    }), callback);
                });
                return Ox.clone(data, true);
            },
            keys: ['clips', 'duration', 'editable', 'id', 'modified', 'posterRatio', 'videoRatio', 'streams'].concat(pandora.site.itemTitleKeys),
            selected: ui.listSelection,
            size: 192,
            sort: ui.listSort,
            unique: 'id',
            width: window.innerWidth
                - ui.showSidebar * ui.sidebarSize - 1
                - Ox.UI.SCROLLBAR_SIZE
        })
        .addClass('OxMedia')
        .bindEvent({
            key_left: function() {
                // ...
            },
            key_right: function() {
                // ...
            }
        });
    } else if (view == 'timelines') {
        that = Ox.InfoList({
            borderRadius: ui.icons == 'posters' ? 0 : 16,
            defaultRatio: ui.icons == 'posters' ? pandora.site.posters.ratio : 1,
            draggable: true,
            id: 'list',
            item: function(data, sort, size) {
                size = 128;
                var clipsQuery = pandora.getClipsQuery(),
                    isClipsQuery = clipsQuery.conditions.length > 1,
                    ratio = ui.icons == 'posters'
                        ? (ui.showSitePosters ? pandora.site.posters.ratio : data.posterRatio) : 1,
                    url = pandora.getMediaURL('/' + data.id + '/' + (
                        ui.icons == 'posters'
                        ? (ui.showSitePosters ? 'siteposter' : 'poster') : 'icon'
                    ) + size + '.jpg?' + data.modified),
                    format, info, sortKey = sort[0].key;
                if (['title', 'director'].indexOf(sortKey) > -1) {
                    info = data['year'] || data['date'] || '';
                } else {
                    format = pandora.getSortKeyData(sortKey).format;
                    if (Ox.isUndefined(data[sortKey]) || Ox.isNull(data[sortKey])) {
                        info = '';
                    } else if (format) {
                        info = (
                            /^color/.test(format.type.toLowerCase()) ? Ox.Theme : Ox
                        )['format' + Ox.toTitleCase(format.type)].apply(
                            this, [data[sortKey]].concat(format.args || [])
                        );
                        if (sortKey == 'rightslevel') {
                            info.css({width: size * 0.75 + 'px'});
                        }
                    } else {
                        info = data[sortKey] || '';
                    }
                }
                return {
                    icon: {
                        height: Math.round(ratio <= 1 ? size : size / ratio),
                        id: data.id,
                        info: info,
                        title: pandora.getItemTitle(data),
                        url: url,
                        width: Math.round(ratio >= 1 ? size : size * ratio)
                    },
                    info: data.rendered ? {
                        css: {marginTop: '2px'},
                        element: Ox.BlockVideoTimeline,
                        events: {
                            position: function(event) {
                                if (ui.videoPoints[data.id]) {
                                    pandora.UI.set('videoPoints.' + data.id + '.position', event.position);
                                } else {
                                    pandora.UI.set('videoPoints.' + data.id, {'in': 0, out: 0, position: event.position});
                                }
                                // FIXME: we need a way to set the position
                                // once the video preview has loaded
                                pandora.$ui.videoPreview && pandora.$ui.videoPreview.options({
                                    position: event.position
                                });
                            }
                        },
                        id: data.id,
                        options: {
                            duration: data.duration,
                            find: isClipsQuery ? clipsQuery.conditions[0].value : '',
                            getImageURL: function(type, i) {
                                return pandora.getMediaURL(
                                    '/' + data.id + '/timeline' + type + '16p' + i + '.jpg'
                                );
                            },
                            position: ui.videoPoints[data.id]
                                ? ui.videoPoints[data.id].position : 0,
                            results: isClipsQuery ? data.clips.map(function(clip) {
                                return {'in': clip['in'], out: clip.out};
                            }) : [],
                            subtitles: isClipsQuery ? data.clips.map(function(clip) {
                                return {'in': clip['in'], out: clip.out, text: clip.annotations[0].value};
                            }) : [],
                            type: ui.videoTimeline
                        }
                    } : {
                        css: {marginTop: '2px'},
                        element: Ox.Element,
                        id: data.id,
                        options: {}
                    }
                };
            },
            items: function(data, callback) {
                var clipsQuery = pandora.getClipsQuery(),
                    isClipsQuery = clipsQuery.conditions.length > 1;
                pandora.api.find(Ox.extend(data, Ox.extend({
                    query: ui.find
                }, isClipsQuery ? {clips: {
                    query: clipsQuery,
                    items: 1000000,
                    keys: []
                }} : {})), callback);
                return Ox.clone(data, true);
            },
            keys: ['clips', 'duration', 'editable', 'id', 'modified', 'posterRatio', 'rendered'].concat(pandora.site.itemTitleKeys),
            selected: ui.listSelection,
            size: 192,
            sort: ui.listSort,
            unique: 'id'
        })
        .bindEvent({
            key_left: function() {
                // ...
            },
            key_right: function() {
                // ...
            }
        });
    } else if (view == 'maps') {
        that = Ox.Element().css({margin: '16px'}).html(view + ' results view still missing.');
    } else if (view == 'calendars') {
        that = Ox.Element().css({margin: '16px'}).html(view + ' results view still missing.');
    } else if (view == 'clip') {
        that = pandora.$ui.clipList = pandora.ui.clipList();
    } else if (view == 'video') {
        that = pandora.ui.videoView();
    } else if (['map', 'calendar'].indexOf(view) > -1) {
        that = pandora.ui.navigationView(view);
    }

    if (['list', 'grid', 'clip'].indexOf(view) > -1) {
        // react to the resize event of the split panel
        that.bindEvent({
            resize: function(data) {
                that.size();
            }
        });
    }

    if (['list', 'grid', 'clips', 'timelines', 'video'].indexOf(view) > -1) {

        pandora.enableDragAndDrop(that, true);

        that.bindEvent({
            closepreview: function(data) {
                pandora.$ui.previewDialog.close();
                delete pandora.$ui.previewDialog;
            },
            copy: function(data) {
                pandora.clipboard.copy(data.ids, 'item');
            },
            copyadd: function(data) {
                pandora.clipboard.add(data.ids, 'item');
            },
            cut: function(data) {
                var listData = pandora.getListData();
                if (listData.editable && listData.type == 'static') {
                    pandora.clipboard.copy(data.ids, 'item');
                    pandora.doHistory('cut', data.ids, ui._list, function() {
                        pandora.UI.set({listSelection: []});
                        pandora.reloadList();
                    });
                }
            },
            cutadd: function(data) {
                var listData = pandora.getListData();
                if (listData.editable && listData.type == 'static') {
                    pandora.clipboard.add(data.ids, 'item');
                    pandora.doHistory('cut', data.ids, ui._list, function() {
                        pandora.UI.set({listSelection: []});
                        pandora.reloadList();
                    });
                }
            },
            'delete': function(data) {
                var listData = pandora.getListData();
                if (listData.editable && listData.type == 'static') {
                    pandora.doHistory('delete', data.ids, ui._list, function() {
                        pandora.UI.set({listSelection: []});
                        pandora.reloadList();
                    });
                }
            },
            init: function(data) {
                var folder, list;
                if (data.query.conditions.length == 0) {
                    pandora.$ui.allItems.update(data.items);
                } else if (
                    data.query.conditions.length == 1
                    && data.query.conditions[0].key == 'list'
                    && data.query.conditions[0].operator == '=='
                ) {
                    list = data.query.conditions[0].value;
                    folder = pandora.getListData(list).folder;
                    if (pandora.$ui.folderList[folder]
                        && !Ox.isEmpty(pandora.$ui.folderList[folder].value(list))) {
                        pandora.$ui.folderList[folder].value(
                            list, 'items', data.items
                        );
                    }
                }
                pandora.$ui.statusbar.set('total', data);
                data = [];
                pandora.site.totals.forEach(function(v) {
                    data[v.id] = 0;
                });
                pandora.$ui.statusbar.set('selected', data);
            },
            open: function(data) {
                var set = {item: data.ids[0]};
                if (data.isSpecialTarget) {
                    set.itemView = ui.videoView;
                }
                if (['accessed', 'timesaccessed'].indexOf(ui.listSort[0].key) > -1) {
                    Ox.Request.clearCache('find');
                }
                pandora.UI.set(set);
            },
            openpreview: function(data) {
                if (!pandora.$ui.previewDialog) {
                    pandora.$ui.previewDialog = pandora.ui.previewDialog()
                        .open()
                        .bindEvent({
                            close: function() {
                                that.closePreview();
                                delete pandora.$ui.previewDialog;
                            }
                        });
                } else {
                    pandora.$ui.previewDialog.update();
                }
            },
            paste: function(data) {
                var items = pandora.clipboard.paste();
                if (items.length && pandora.clipboard.type() == 'item' && pandora.getListData().editable) {
                    pandora.doHistory('paste', items, ui._list, function() {
                        pandora.UI.set({listSelection: items});
                        pandora.reloadList();
                    });
                }
            },
            select: function(data) {
                var query;
                pandora.UI.set('listSelection', data.ids);
                if (data.ids.length == 0) {
                    pandora.$ui.statusbar.set('selected', {items: 0});
                } else {
                    if (Ox.isUndefined(data.rest)) {
                        query = {
                            conditions: data.ids.map(function(id) {
                                return {
                                    key: 'id',
                                    value: id,
                                    operator: '=='
                                }
                            }),
                            operator: '|'
                        };
                    } else {
                        query = {
                            conditions: [ui.find].concat(
                                data.rest.map(function(id) {
                                    return {
                                        key: 'id',
                                        value: id,
                                        operator: '!='
                                    };
                                })
                            ),
                            operator: '&'
                        };
                    }
                    pandora.api.find({
                        query: query
                    }, function(result) {
                        pandora.$ui.statusbar.set('selected', result.data);
                    });
                }
            },
            pandora_listselection: function(data) {
                that.options({selected: data.value});
            },
            pandora_listsort: function(data) {
                that.options({sort: data.value});
            }
        });

    }

    if (['list', 'grid', 'timelines'].indexOf(view) > -1) {
        that.bindEvent({
            pandora_icons: function(data) {
                var src, previousSrc;
                // fixme: doesn't update title icon, passes useless options
                if (hasIcons()) {
                    if (ui.listView == 'list') {
                        src = Ox.UI.getImageURL(
                            data.value == 'posters' ? 'symbolSetPoster' : 'symbolIcon'
                        );
                        previousSrc = Ox.UI.getImageURL(
                            data.previousValue == 'posters' ? 'symbolSetPoster' : 'symbolIcon'
                        );
                        that.find('img[src="' + previousSrc + '"]').attr({src: src});
                    } else {
                        that.options({
                            borderRadius: data.value == 'posters' ? 0 : 16,
                            defaultRatio: data.value == 'posters' ? pandora.site.posters.ratio : 1
                        });
                    }
                    that.reloadList(true);
                }
            },
            pandora_showsiteposters: function() {
                // fixme: should be disabled if ui.icons != 'posters'
                hasIcons() && ui.icons == 'posters' && that.reloadList(true);
            }
        });
    }

    if (view == 'timelines') {
        that.bindEvent({
            pandora_videotimeline: function(data) {
                that.reloadList(true);
            }
        });
    }

    function hasIcons() {
        return (
            ui.listView == 'list'
            && ui.listColumns.indexOf('posterRatio') > -1
        ) || ['grid', 'timelines'].indexOf(ui.listView) > -1;
    }

    return that;

};

