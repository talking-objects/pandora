// vim: et:ts=4:sw=4:sts=4:ft=javascript

pandora.ui.list = function() { // fixme: remove view argument
    var that, $map,
        view = pandora.user.ui.lists[pandora.user.ui.list].listView,
        preview = false
    //Ox.print('constructList', view);
    if (view == 'list') {
        /*
        keys = Ox.unique(Ox.merge(
            $.map(pandora.user.ui.lists[pandora.user.ui.list].columns, function(id) {
                return Ox.getObjectById(pandora.site.sortKeys, id);
            }),
            pandora.site.sortKeys
        ));
        Ox.print('$$$$', keys)
        */
        that = Ox.TextList({
            columns: /*Ox.merge([{
                align: 'center',
                defaultWidth: 16,
                format: function(value, data) {
                    var icon, width, height, margin, marginCSS, borderRadius;
                    if (pandora.user.ui.icons == 'posters') {
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
                        })
                    }).attr({
                        src: '/' + data.id + '/' + icon + '14.jpg'
                    });
                },
                id: 'posterRatio',
                operator: '+',
                position: 0,
                removable: true,
                title: 'Poster',
                *//*
                title: $('<img>').attr({
                        src: Ox.UI.getImageURL(
                            pandora.user.ui.icons == 'posters'
                            ? 'symbolSetPoster' : 'symbolIcon'
                        )
                    })
                    .css({
                        width: '12px',
                        height: '12px',
                        padding: '2px',
                    }),
                *//*
                visible: true,
                width: 16
            }], */Ox.map(pandora.site.sortKeys, function(key) {
                var position = pandora.user.ui.lists[pandora.user.ui.list].columns.indexOf(key.id);
                return {
                    align: ['string', 'text'].indexOf(
                        Ox.isArray(key.type) ? key.type[0]: key.type
                    ) > -1 ? 'left' : 'right',
                    defaultWidth: key.columnWidth,
                    format: key.format,
                    id: key.id,
                    operator: pandora.getSortOperator(key.id),
                    position: position,
                    removable: !key.columnRequired,
                    title: key.title,
                    type: key.type,
                    unique: key.id == 'id',
                    visible: position > -1,
                    width: pandora.user.ui.lists[pandora.user.ui.list].columnWidth[key.id] || key.columnWidth
                };
            })/*)*/,
            columnsMovable: true,
            columnsRemovable: true,
            columnsResizable: true,
            columnsVisible: true,
            draggable: true,
            id: 'list',
            items: function(data, callback) {
                //Ox.print('data, pandora.Query.toObject', data, pandora.Query.toObject())
                pandora.api.find(Ox.extend(data, {
                    query: pandora.user.ui.query
                }), callback);
            },
            scrollbarVisible: true,
            selected: pandora.user.ui.lists[pandora.user.ui.list].selected,
            sort: pandora.user.ui.lists[pandora.user.ui.list].sort
        })
        .bindEvent({
            columnchange: function(data) {
                var columnWidth = {};
                pandora.UI.set(['lists', pandora.user.ui.list, 'columns'].join('|'), data.ids);
                /*
                data.ids.forEach(function(id) {
                    columnWidth[id] = 
                        pandora.user.ui.lists[pandora.user.ui.list].columnWidth[id] ||
                        Ox.getObjectById(pandora.site.sortKeys, id).width
                });
                pandora.UI.set(['lists', pandora.user.ui.list, 'columnWidth'].join('|'), columnWidth);
                */
            },
            columnresize: function(data) {
                pandora.UI.set(['lists', pandora.user.ui.list, 'columnWidth', data.id].join('|'), data.width);
            },
            resize: function(data) { // this is the resize event of the split panel
                that.size();
            },
            sort: function(data) {
                Ox.print('---- SORT ----', data)
                pandora.$ui.mainMenu.checkItem('sortMenu_sortmovies_' + data.key);
                pandora.$ui.mainMenu.checkItem('sortMenu_ordermovies_' + (data.operator == '+' ? 'ascending' : 'descending'));
                pandora.$ui.sortSelect.selectItem(data.key);
                pandora.UI.set(['lists', pandora.user.ui.list, 'sort'].join('|'), [{key: data.key, operator: data.operator}]);
                pandora.URL.push(pandora.Query.toString());
            }
        });
    } else if (view == 'grid') {
        //alert(JSON.stringify(pandora.user.ui.lists[pandora.user.ui.list].selected))
        that = Ox.IconList({
            borderRadius: pandora.user.ui.icons == 'posters' ? 0 : 16,
            defaultRatio: pandora.user.ui.icons == 'posters' ? 5/8 : 1,
            draggable: true,
            id: 'list',
            item: function(data, sort, size) {
                var icons = pandora.user.ui.icons,
                    ratio = icons == 'posters' ? data.posterRatio : 1;
                size = size || 128;
                return {
                    height: Math.round(ratio <= 1 ? size : size / ratio),
                    id: data.id,
                    info: data[['title', 'director'].indexOf(sort[0].key) > -1 ? 'year' : sort[0].key],
                    title: data.title + (data.director.length ? ' (' + data.director.join(', ') + ')' : ''),
                    url: icons == 'posters' 
                        ? '/' + data.id + '/poster' + size + '.jpg'
                        : '/' + data.id + '/icon' + size + '.jpg',
                    width: Math.round(ratio >= 1 ? size : size * ratio)
                };
            },
            items: function(data, callback) {
                //Ox.print('data, pandora.Query.toObject', data, pandora.Query.toObject())
                pandora.api.find(Ox.extend(data, {
                    query: pandora.user.ui.query
                }), callback);
            },
            keys: ['director', 'id', 'posterRatio', 'title', 'year'],
            selected: pandora.user.ui.lists[pandora.user.ui.list].selected,
            size: 128,
            sort: pandora.user.ui.lists[pandora.user.ui.list].sort,
            unique: 'id'
        });
    } else if (view == 'info') {
        that = Ox.Element().css({margin: '16px'}).html(view + ' results view still missing.');
    } else if (view == 'clips') {
        that = Ox.Element().css({margin: '16px'}).html(view + ' results view still missing.');
    } else if (view == 'timelines') {
        that = Ox.InfoList({
            borderRadius: pandora.user.ui.icons == 'posters' ? 0 : 16,
            defaultRatio: pandora.user.ui.icons == 'posters' ? 5/8 : 1,
            id: 'list',
            item: function(data, sort, size) {
                var icons = pandora.user.ui.icons,
                    ratio = icons == 'posters' ? data.posterRatio : 1;
                size = 128;
                return {
                    icon: {
                        height: ratio <= 1 ? size : size / ratio,
                        id: data.id,
                        info: data[['title', 'director'].indexOf(sort[0].key) > -1 ? 'year' : sort[0].key],
                        title: data.title + (data.director.length ? ' (' + data.director.join(', ') + ')' : ''),
                        url: icons == 'posters' 
                            ? '/' + data.id + '/poster' + size + '.jpg'
                            : '/' + data.id + '/icon' + size + '.jpg',
                        width: ratio >= 1 ? size : size * ratio    
                    },
                    info: {
                        css: {
                            margin: '-4px 0 0 -4px'
                        },
                        element: Ox.BlockVideoTimeline,
                        id: data.id,
                        options: {
                            duration: data.duration,
                            getImageURL: '/' + data.id + '/timeline16p.png'                            
                        }
                    }
                };
            },
            items: function(data, callback) {
                pandora.api.find(Ox.extend(data, {
                    query: pandora.user.ui.query
                }), callback);
            },
            keys: ['director', 'duration', 'id', 'posterRatio', 'title', 'year'],
            selected: pandora.user.ui.lists[pandora.user.ui.list].selected,
            size: 192,
            sort: pandora.user.ui.lists[pandora.user.ui.list].sort,
            unique: 'id'
        });        
    } else if (view == 'maps') {
        that = Ox.Element().css({margin: '16px'}).html(view + ' results view still missing.');
    } else if (view == 'calendars') {
        that = Ox.Element().css({margin: '16px'}).html(view + ' results view still missing.');
    } else if (view == 'clip') {
        var fixedRatio = 16/9;
        that = Ox.IconList({
            fixedRatio: fixedRatio,
            item: function(data, sort, size) {
                size = size || 128;
                var ratio = data.videoRatio,
                    width = ratio > fixedRatio ? size : Math.round(size * ratio / fixedRatio),
                    height = Math.round(width / ratio),
                    url = '/' + data.id.split('/')[0] + '/' + height + 'p' + data['in'] + '.jpg';
                return {
                    height: height,
                    id: data.id,
                    info: Ox.formatDuration(data['in'], 'short') + ' - ' + Ox.formatDuration(data['out'], 'short'),
                    title: data.value,
                    url: url,
                    width: width
                };
            },
            items: function(data, callback) {
                var itemQuery = pandora.user.ui.query,
                    query = {conditions:[]};
                //fixme: can this be in pandora.Query? dont just check for subtitles
                itemQuery.conditions.forEach(function(q) {
                    if (q.key == 'subtitles') {
                        query.conditions.push({key: 'value', value: q.value, operator: q.operator});
                    }
                });
                pandora.api.findAnnotations(Ox.extend({
                    query: query,
                    itemQuery: itemQuery
                }, data), callback);
            },
            keys: ['id', 'value', 'in', 'out', 'videoRatio'],
            max: 1,
            size: 128,
            sort: pandora.user.ui.lists[pandora.user.ui.list].sort,
            unique: 'id'
        }).bindEvent({
            init: function(data) {
                pandora.$ui.total.html(pandora.ui.status('total', data));
            },
            open: function(data) {
                var id = data.ids[0],
                    item = id.split('/')[0],
                    points = {
                        'in': that.value(id, 'in'),
                        out: that.value(id, 'out')
                    };
                pandora.UI.set('videoPoints|' + item, Ox.extend(points, {
                    position: points['in']
                }));
                pandora.URL.set(item + '/timeline');
            },
            openpreview: function(data) {
                var $video = $('.OxItem.OxSelected > .OxIcon > .OxVideoPlayer');
                if ($video) {
                    // trigger singleclick
                    $video.trigger('mousedown');
                    Ox.UI.$window.trigger('mouseup');
                }
                that.closePreview();
            },
            select: function(data) {
                if (data.ids.length) {
                    var id = data.ids[0],
                        item = id.split('/')[0], width, height,
                        $img = $('.OxItem.OxSelected > .OxIcon > img'),
                        $video = $('.OxItem.OxSelected > .OxIcon > .OxVideoPlayer');
                    pandora.UI.set('lists|' + pandora.user.ui.list + '|selected', [item]);
                    pandora.$ui.leftPanel.replaceElement(2, pandora.$ui.info = pandora.ui.info());
                    if ($img.length) {
                        var width = parseInt($img.css('width')),
                            height = parseInt($img.css('height'));
                        pandora.api.get({id: item, keys: ['durations']}, function(result) {
                            var points = [that.value(id, 'in'), that.value(id, 'out')],
                                partsAndPoints = pandora.getVideoPartsAndPoints(result.data.durations, points),
                                $player = Ox.VideoPlayer({
                                    height: height,
                                    'in': partsAndPoints.points[0],
                                    out: partsAndPoints.points[1],
                                    paused: true,
                                    playInToOut: true,
                                    poster: '/' + item + '/' + height + 'p' + points[0] + '.jpg',
                                    width: width,
                                    video: partsAndPoints.parts.map(function(i) {
                                        return '/' + item + '/96p' + (i + 1) + '.' + pandora.user.videoFormat;
                                    })
                                })
                                .addClass('OxTarget')
                                .bindEvent({
                                    // doubleclick opens item
                                    singleclick: function() {
                                        $player.$element.is('.OxSelectedVideo') && $player.togglePaused();
                                    }
                                });
                            $img.replaceWith($player.$element);
                            $('.OxSelectedVideo').removeClass('OxSelectedVideo');
                            $player.$element.addClass('OxSelectedVideo');
                        });
                    } else if ($video.length) {
                        // item select fires before video click
                        // so we have to make sure that selecting
                        // doesn't click through to play
                        setTimeout(function() {
                            $('.OxSelectedVideo').removeClass('OxSelectedVideo');
                            $video.addClass('OxSelectedVideo');
                        }, 300);
                    }
                } else {
                    pandora.UI.set('lists|' + pandora.user.ui.list + '|selected', []);
                    pandora.$ui.leftPanel.replaceElement(2, pandora.$ui.info = pandora.ui.info());
                    $('.OxSelectedVideo').removeClass('OxSelectedVideo');
                }
            }
        });
    } else if (view == 'player') {
        that = Ox.VideoPlayer({
            controlsBottom: ['play', 'previous', 'next', 'volume'],
            controlsTop: ['fullscreen', 'scale'],
            enableMouse: true,
            height: 384,
            paused: true,
            position: 0,
            video: function(range, callback) {
                var callback = arguments[arguments.length - 1],
                    range = arguments.length == 2 ? arguments[0] : null,
                    itemQuery = pandora.user.ui.query,
                    query = {conditions:[]};
                //fixme: can this be in pandora.Query? dont just check for subtitles
                itemQuery.conditions.forEach(function(q) {
                    if (q.key == 'subtitles') {
                        query.conditions.push({key: 'value', value: q.value, operator: q.operator});
                    }
                });
                pandora.api.findAnnotations(Ox.extend({
                    query: query,
                    itemQuery: itemQuery
                }, range ? {
                    keys: ['id', 'in', 'out'],
                    range: range,
                    sort: pandora.user.ui.lists[pandora.user.ui.list].sort
                } : {}), function(result) {
                    //Ox.print('API findAnnotations range', range, 'result', result.data);
                    if (!range) {
                        callback(result.data.items);
                    } else {
                        var counter = 0,
                            length = range[1] - range[0],
                            data = [];
                        result.data.items.forEach(function(item, i) {
                            var id = item.id.split('/')[0]
                            pandora.api.get({id: id, keys: ['durations']}, function(result) {
                                //Ox.print('API get item', id, 'result', result.data);
                                var points = [item['in'], item.out],
                                    partsAndPoints = pandora.getVideoPartsAndPoints(result.data.durations, points);                       
                                data[i] = {
                                    parts: partsAndPoints.parts.map(function(i) {
                                        return '/' + id + '/96p' + (i + 1) + '.' + pandora.user.videoFormat;
                                    }),
                                    points: partsAndPoints.points
                                }
                                if (++counter == length) {
                                    callback(data);
                                }
                            });
                        });
                    }
                });
            },
            width: 512
        });
    } else if (view == 'map') {
        var fixedRatio = 16/9;
        that = Ox.SplitPanel({
            elements: [
                {
                    element: pandora.$ui.map = Ox.Map({
                        height: window.innerHeight - pandora.user.ui.showGroups * pandora.user.ui.groupsSize - 61,
                        places: function(data, callback) {
                            var itemQuery = pandora.user.ui.query,
                                query = {conditions:[]};
                            return pandora.api.findPlaces(Ox.extend(data, {
                                itemQuery: itemQuery,
                                query: query
                            }), callback);
                        },
                        showTypes: true,
                        toolbar: true,
                        width: window.innerWidth - pandora.user.ui.showSidebar * pandora.user.ui.sidebarSize - 2 - 144 - Ox.UI.SCROLLBAR_SIZE,
                    }).bindEvent({
                        selectplace: function(event, place) {
                            if(place && place.id[0] != '_') {
                                pandora.$ui.clips.options({
                                    items: function(data, callback) {
                                        return pandora.api.findAnnotations(Ox.extend(data, {
                                            query: {
                                                conditions:[{key: 'place', value: place.id, operator:'='}]
                                            },
                                            itemQuery: pandora.user.ui.query
                                        }), callback);
                                    }
                                });
                            } else {
                                pandora.$ui.clips.options({
                                    items: []
                                });
                            }
                        }
                    })
                },
                {
                    element: pandora.$ui.clips = Ox.IconList({
                        fixedRatio: fixedRatio,
                        item: function(data, sort, size) {
                            Ox.print('RATIO', data.videoRatio);
                            size = size || 128;
                            var width = data.videoRatio < fixedRatio ? size : size * data.videoRatio / fixedRatio,
                                height = width / data.videoRatio,
                                url = '/' + data.item + '/' + height + 'p' + data['in'] + '.jpg';
                            return {
                                height: height,
                                id: data.id,
                                info: Ox.formatDuration(data['in'], 'short') + ' - '
                                    + Ox.formatDuration(data['out'], 'short'),
                                title: data.value,
                                url: url,
                                width: width
                            };
                        },
                        items: [],
                        keys: ['id', 'value', 'in', 'out', 'videoRatio', 'item'],
                        size: 128,
                        sort: pandora.user.ui.lists[pandora.user.ui.list].sort,
                        unique: 'id'
                    }).bindEvent({
                        open: function(data) {
                            var id = data.ids[0],
                                item = pandora.$ui.clips.value(id, 'item'),
                                points = {
                                    'in': pandora.$ui.clips.value(id, 'in'),
                                    out: pandora.$ui.clips.value(id, 'out')
                                };
                            pandora.UI.set('videoPoints|' + item, Ox.extend(points, {
                                position: points['in']
                            }));
                            pandora.URL.set(item + '/timeline');
                        }
                    }),
                    id: 'place',
                    size: 144 + Ox.UI.SCROLLBAR_SIZE
                }
            ],
            orientation: 'horizontal'
        })
        .bindEvent('resize', function() {
            pandora.$ui.map.resizeMap();
        });
    } else if (view == 'calendar') {
        that = Ox.SplitPanel({
            elements: [
                {
                    element: pandora.$ui.calendar = Ox.Element()
                },
                {
                    element: Ox.Element(),
                    id: 'place',
                    size: 144 + Ox.UI.SCROLLBAR_SIZE
                }
            ],
            orientation: 'horizontal'
        })
        .bindEvent('resize', function(data) {

        });
        pandora.api.findEvents({
            itemQuery: pandora.user.ui.query,
            keys: ['id', 'name', 'start', 'end'],
            query: {}
        }, function(result) {
            that.replaceElement(0, pandora.$ui.calendar = Ox.Calendar({
                date: new Date(0),
                events: result.data.items,
                height: window.innerHeight - pandora.user.ui.showGroups * pandora.user.ui.groupsSize - 61,
                range: [-5000, 5000],
                width: window.innerWidth - pandora.user.ui.showSidebar * pandora.user.ui.sidebarSize - 2 - 144 - Ox.UI.SCROLLBAR_SIZE,
                zoom: 4
            }));
        });
    } else {
        // fixme: ???
        $list = Ox.Element('<div>')
            .css({
                width: '100px',
                height: '100px',
                background: 'red'
            });
    }

    if (['list', 'grid'].indexOf(view) > -1) {

        pandora.enableDragAndDrop(that, true);

        that.bindEvent({
            closepreview: function(data) {
                pandora.$ui.previewDialog.close();
                preview = false;
                //delete pandora.$ui.previewDialog;
            },
            copy: function(data) {
                Ox.Clipboard.copy({
                    items: data.ids,
                    text: data.ids.map(function(id) {
                        return pandora.$ui.list.value(id, 'title');
                    }).join('\n')
                });
            },
            'delete': function(data) {
                pandora.getListData().editable && pandora.api.removeListItems({
                    list: pandora.user.ui.list,
                    items: data.ids
                }, pandora.reloadList);
            },
            init: function(data) {
                pandora.$ui.total.html(pandora.ui.status('total', data));
                data = [];
                pandora.site.totals.forEach(function(v) {
                    data[v.id] = 0;
                });
                pandora.$ui.selected.html(pandora.ui.status('selected', data));
            },
            open: function(data) {
                var id = data.ids[0],
                    title = that.value(id, 'title');
                pandora.URL.set(title, id);
            },
            openpreview: function(data) {
                pandora.requests.preview && pandora.api.cancel(pandora.requests.preview);
                pandora.requests.preview = pandora.api.find({
                    keys: ['director', 'id', 'posterRatio', 'title'],
                    query: {
                        conditions: data.ids.map(function(id) {
                            return {
                                key: 'id',
                                value: id,
                                operator: '='
                            }
                        }),
                        operator: '|'
                    }
                }, function(result) {
                    var item = result.data.items[0],
                        title = item.title + ' (' + item.director + ')'
                        ratio = item.posterRatio,
                        windowWidth = window.innerWidth * 0.8,
                        windowHeight = window.innerHeight * 0.8,
                        windowRatio = windowWidth / windowHeight,
                        width = Math.round(ratio > windowRatio ? windowWidth : windowHeight * ratio),
                        height = Math.round(ratio < windowRatio ? windowHeight : windowWidth / ratio);
                    pandora.$ui.previewImage = $('<img>')
                        .attr({src: '/' + item.id + '/poster128.jpg'})
                        .css({width: width + 'px', height: height + 'px'})
                    $('<img>').load(function() {
                            pandora.$ui.previewImage.attr({src: $(this).attr('src')});
                        })
                        .attr({src: '/' + item.id + '/poster1024.jpg'});
                    if (!preview) {
                        if (!pandora.$ui.previewDialog) {
                            pandora.$ui.previewDialog = Ox.Dialog({
                                    closeButton: true,
                                    content: pandora.$ui.previewImage,
                                    fixedRatio: true,
                                    focus: false,
                                    height: height,
                                    maximizeButton: true,
                                    title: title,
                                    width: width
                                })
                                .bindEvent({
                                    close: function() {
                                        that.closePreview();
                                        preview = false;
                                    },
                                    resize: function(data) {
                                        pandora.$ui.previewImage.css({
                                            width: data.width + 'px',
                                            height: data.height + 'px'
                                        });
                                    }
                                })
                                .open();
                        } else {
                                pandora.$ui.previewDialog.options({
                                    content: pandora.$ui.previewImage,
                                    height: height,
                                    title: title,
                                    width: width
                                })
                                .open();
                        }
                        preview = true;
                    } else {
                        pandora.$ui.previewDialog.options({
                                content: pandora.$ui.previewImage,
                                title: title,
                            })
                            .setSize(width, height);
                    }
                });
            },
            paste: function(data) {
                data.items && pandora.getListData().editable && pandora.api.addListItems({
                    list: pandora.user.ui.list,
                    items: data.items
                }, pandora.reloadList);
            },
            select: function(data) {
                var $still, $timeline;
                pandora.UI.set('lists|' + pandora.user.ui.list + '|selected', data.ids);
                if (data.ids.length) {
                    pandora.$ui.mainMenu.enableItem('copy');
                    pandora.$ui.mainMenu.enableItem('openmovie');
                } else {
                    pandora.$ui.mainMenu.disableItem('copy');
                    pandora.$ui.mainMenu.disableItem('openmovie');            
                }
                pandora.$ui.leftPanel.replaceElement(2, pandora.$ui.info = pandora.ui.info());
                pandora.api.find({
                    query: {
                        conditions: data.ids.map(function(id) {
                            return {
                                key: 'id',
                                value: id,
                                operator: '='
                            }
                        }),
                        operator: '|'
                    }
                }, function(result) {
                    pandora.$ui.selected.html(pandora.ui.status('selected', result.data));
                });
            }
        });
        
    }

    that.display = function() { // fixme: used?
        pandora.$ui.rightPanel.replaceElement(1, pandora.$ui.contentPanel = pandora.ui.contentPanel());
    };

    return that;

};

