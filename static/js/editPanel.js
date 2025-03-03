'use strict';

pandora.ui.editPanel = function(isEmbed) {

    var ui = pandora.user.ui,
        edit,
        smallTimelineCanvas,
        smallTimelineContext,
        that = Ox.Element();

    ui.edit ? getEdit(isEmbed ? renderEmbedEdit : renderEdit) : renderEdits();

    function editsKey(key) {
        return 'edits.' + ui.edit.replace(/\./g, '\\.') + '.' + key;
    }

    function enableDragAndDrop() {
        pandora.enableDragAndDrop(
            Ox.$elements[that.find('.OxIconList').data('oxid')],
            edit.editable,
            'edits',
            function($list) {
                return serializeClips($list.options('selected')).map(function(id) {
                    return id.split('/').slice(0, 2).join('/');
                });
            }
        );
    }

    function getClips(ids) {
        return ids.map(function(id) {
            return Ox.getObjectById(edit.clips, id);
        });
    }

    function getEdit(callback) {
        pandora.api.getEdit({id: ui.edit}, function(result) {
            edit = result.data;
            sortClips(callback);
        });
    }

    function getSmallTimelineCanvas() {
        var fps = getSmallTimelineFPS(),
            width = Math.ceil(edit.duration * fps),
            height = fps == 1 ? 16 : 64;
        return Ox.$('<canvas>').attr({width: width, height: height})[0];
    }

    function getSmallTimelineFPS() {
        return Math.floor(edit.duration * 25) < 32768 ? 25 : 1;
    }

    function getSmallTimelineURL() {
        if (!edit.duration) {
            return ''
        }
        smallTimelineCanvas = getSmallTimelineCanvas();
        smallTimelineContext = smallTimelineCanvas.getContext('2d');
        return smallTimelineCanvas.toDataURL();
    }

    function getVideos() {
        var videos = [];
        edit.clips.filter(function(clip) {
            return clip.duration;
        }).map(function(clip) {
            pandora.site.video.resolutions.forEach(function(resolution) {
                videos = videos.concat(pandora.getClipVideos(clip, resolution));
            });
        });
        return videos;
    }

    function renderEdit() {
        if (ui.section != 'edits' || ui.edit != edit.id) {
            return;
        }
        var editSettings = ui.edits[ui.edit] || pandora.site.editSettings
        that = pandora.$ui.editPanel = Ox.VideoEditPanel({
            annotationsCalendarSize: ui.annotationsCalendarSize,
            annotationsMapSize: ui.annotationsMapSize,
            annotationsRange: ui.annotationsRange,
            annotationsSort: ui.annotationsSort,
            clickLink: pandora.clickLink,
            clipRatio: pandora.site.video.previewRatio,
            clips: Ox.clone(edit.clips),
            clipSize: ui.clipSize + Ox.UI.SCROLLBAR_SIZE,
            clipTooltip: 'clips <span class="OxBright">' + Ox.SYMBOLS.shift + 'C</span>',
            clipView: editSettings.view,
            controlsTooltips: {
                open: Ox._('Open in {0} View', [Ox._(Ox.getObjectById(
                    pandora.site.itemViews, pandora.user.ui.videoView
                ).title)])
            },
            duration: edit.duration,
            editable: edit.type == 'static' && edit.editable,
            enableSubtitles: ui.videoSubtitles,
            formatTitle: function() {
                return pandora.getItemTitle(Ox.last(arguments), true);
            },
            fullscreen: false,
            getClipImageURL: function(id, width, height) {
                var clip = Ox.getObjectById(edit.clips, id);
                return pandora.getMediaURL('/' + clip.item + '/' + height + 'p' + clip['in'] + '.jpg');
            },
            getLargeTimelineURL: function(type, i, callback) {
                pandora.getLargeEditTimelineURL(edit, type, i, callback);
            },
            height: pandora.$ui.appPanel.size(1),
            'in': editSettings['in'],
            layers: getLayers(edit.clips),
            loop: ui.videoLoop,
            muted: ui.videoMuted,
            out: editSettings.out,
            position: editSettings.position,
            resolution: ui.videoResolution,
            scaleToFill: ui.videoScale == 'fill',
            selected: editSettings.selection,
            showAnnotationsCalendar: ui.showAnnotationsCalendar,
            showAnnotationsMap: ui.showAnnotationsMap,
            showClips: ui.showClips,
            showLayers: ui.showLayers,
            showTimeline: ui.showTimeline,
            showUsers: pandora.site.annotations.showUsers,
            smallTimelineURL: getSmallTimelineURL(),
            sort: editSettings.sort,
            sortOptions: (
                    edit.type == 'static'
                    ? [{id: 'index', title: Ox._('Sort Manually'), operator: '+'}]
                    : []
                )
                .concat(
                    pandora.site.clipKeys.map(function(key) {
                        return Ox.extend(Ox.clone(key), {
                            title: Ox._(('Sort by Clip {0}'), [Ox._(key.title)])
                        });
                    })
                ).concat(
                    pandora.site.sortKeys.map(function(key) {
                        return Ox.extend(Ox.clone(key), {
                            title: Ox._('Sort by {0}', [Ox._(key.title)])
                        });
                    })
                ),
            subtitles: getSubtitles(edit.clips),
            subtitlesOffset: ui.videoSubtitlesOffset,
            timeline: ui.videoTimeline,
            timelineTooltip: Ox._('timeline') + ' <span class="OxBright">' + Ox.SYMBOLS.shift + 'T</span>',
            video: getVideos(),
            volume: ui.videoVolume,
            width: Ox.$document.width() - pandora.$ui.mainPanel.size(0) - 1
        })
        .bindEvent({
            clipSize: function(data) {
                pandora.UI.set({clipSize: data.size - Ox.UI.SCROLLBAR_SIZE});
            },
            copy: function(data) {
                var ids = Ox.sort(data.ids, function(id) {
                    return Ox.getObjectById(edit.clips, id).index;
                });
                pandora.clipboard.copy(serializeClips(ids), 'clip');
            },
            copyadd: function(data) {
                var ids = Ox.sort(data.ids, function(id) {
                    return Ox.getObjectById(edit.clips, id).index;
                });
                pandora.clipboard.add(serializeClips(ids), 'clip');
            },
            cut: function(data) {
                var ids = Ox.sort(data.ids, function(id) {
                    return Ox.getObjectById(edit.clips, id).index;
                });
                var clips = serializeClips(ids);
                pandora.clipboard.copy(clips, 'clip');
                pandora.doHistory('cut', clips, ui.edit, function(result) {
                    Ox.Request.clearCache('getEdit');
                    Ox.Request.clearCache('sortClips');
                    updateClips(result.data.clips);
                });
            },
            cutadd: function(data) {
                var ids = Ox.sort(data.ids, function(id) {
                    return Ox.getObjectById(edit.clips, id).index;
                });
                var clips = serializeClips(ids);
                pandora.clipboard.add(clips, 'clip');
                pandora.doHistory('cut', clips, ui.edit, function(result) {
                    Ox.Request.clearCache('getEdit');
                    Ox.Request.clearCache('sortClips');
                    updateClips(result.data.clips);
                });
            },
            'delete': function(data) {
                var ids = Ox.sort(data.ids, function(id) {
                    return Ox.getObjectById(edit.clips, id).index;
                });
                var clips = serializeClips(ids);
                pandora.doHistory('delete', clips, ui.edit, function(result) {
                    Ox.Request.clearCache('getEdit');
                    Ox.Request.clearCache('sortClips');
                    edit.clips = result.data.clips;
                    sortClips(updateClips);
                });
            },
            edit: function(data) {
                var args = {id: data.id},
                    index = Ox.getIndexById(edit.clips, data.id),
                    clip = edit.clips[index];
                if (data.key == 'duration') {
                    data.key = 'out';
                    data.value += clip['in'];
                }
                pandora.api.get({id: clip.item, keys: ['duration']}, function(result) {
                    var clips;
                    //fixme include in history...
                    if (data.key == 'volume') {
                        pandora.api.editClip({
                            id: data.id,
                            volume: data.value
                        }, function(result) {
                            edit.clips[Ox.getIndexById(edit.clips, data.id)] = result.data;
                            Ox.Request.clearCache('sortClips');
                            sortClips(updateClips);
                        });
                        return;
                    }
                    if (data.key == 'out') {
                        data.value = Math.min(data.value, result.data.duration);
                    }
                    clips = serializeClips([data.id]).concat(serializeClips([{
                        id: data.id,
                        'in': data.key == 'in' ? data.value : clip['in'],
                        item: clip.item,
                        out: data.key == 'out' ? data.value : clip.out
                    }]));
                    pandora.doHistory('edit', clips, ui.edit, function(result) {
                        edit.clips[Ox.getIndexById(edit.clips, data.id)] = result.data;
                        Ox.Request.clearCache('sortClips');
                        sortClips(updateClips);
                    });
                });
            },
            join: function(data) {
                var clips = [serializeClips(data.ids), serializeClips(data.join)],
                    index = pandora.$ui.editPanel.getPasteIndex() - 1;
                pandora.doHistory('join', clips, ui.edit, index, function(result) {
                    edit.clips = edit.clips.filter(function(clip) {
                        return !Ox.contains(data.ids, clip.id);
                    }).concat(result.data.clips);
                    sortClips(updateClips);
                });
            },
            loop: function(data) {
                pandora.UI.set({videoLoop: data.loop});
            },
            move: function(data) {
                pandora.api.orderClips({
                    edit: edit.id,
                    ids: data.ids
                }, function(result) {
                    Ox.Request.clearCache('getEdit');
                    Ox.Request.clearCache('sortClips');
                    orderClips(data.ids);
                });
            },
            muted: function(data) {
                pandora.UI.set({videoMuted: data.muted});
            },
            open: function(data) {
                pandora.UI.set(editsKey('clip'), data.ids[0]);
            },
            openlink: function(data) {
                that.options({paused: true});
                pandora.UI.set('videoPoints.' + data.item, data.annotation ? {
                    annotation: data.annotation.split('/')[1],
                    'in': data['in'],
                    out: data.out,
                    position: data.position
                } : {
                    'in': data['in'],
                    out: data.out,
                    position: data.position
                });
                pandora.UI.set({
                    section: 'items',
                    item: data.item || data.annotation.split('/')[0],
                    itemView: ui.videoView,
                });
            },
            paste: function() {
                var clips = pandora.clipboard.paste('clip');
                clips.length && pandora.doHistory('paste', clips, ui.edit, function(result) {
                    Ox.Request.clearCache('getEdit');
                    Ox.Request.clearCache('sortClips');
                    updateClips(edit.clips.map(function(clip) {
                        if (clip.index >= result.data.clips[0].index) {
                            clip.index += result.data.clips.length
                        }
                        return clip;
                    }).concat(result.data.clips));
                    that.options({
                        selected: result.data.clips.map(function(clip) {
                            return clip.id;
                        })
                    });
                });
            },
            playing: function(data) {
                var set = {};
                set[editsKey('clip')] = '';
                set[editsKey('position')] = data.position;
                pandora.UI.set(set);
            },
            position: function(data) {
                var set = {};
                set[editsKey('clip')] = '';
                set[editsKey('position')] = data.position;
                pandora.UI.set(set);
            },
            resize: function(data) {
                // sidebar resize
                that.options({width: data.size});
            },
            resizeclips: function(data) {
                pandora.UI.set({clipsSize: data.clipsSize});
            },
            resolution: function(data) {
                pandora.UI.set({videoResolution: data.resolution});
            },
            scale: function(data) {
                pandora.UI.set({videoScale: data.scale});
            },
            select: function(data) {
                pandora.UI.set({editSelection: data.ids});
            },
            selectannotation: function(data) {
                if ('in' in data) {
                    that.options({position: data['in']})
                }
            },
            sort: function(data) {
                pandora.UI.set({editSort: data});
                sortClips(updateClips);
            },
            split: function(data) {
                var clips = [serializeClips(data.ids), serializeClips(data.split)],
                    index = pandora.$ui.editPanel.getPasteIndex() - 1;
                pandora.doHistory('split', clips, ui.edit, index, function(result) {
                    updateClips(edit.clips.filter(function(clip) {
                        return !Ox.contains(data.ids, clip.id);
                    }).map(function(clip) {
                        if (clip.index >= result.data.clips[0].index) {
                            clip.index += result.data.clips.length
                        }
                        return clip;
                    }).concat(result.data.clips));
                    //fixme: what resets the position here?
                    var position = that.options('position');
                    that.options({
                        selected: result.data.clips.map(function(clip) { return clip.id}),
                    });
                    setTimeout(function() {
                        that.options('position', position);
                    }, 500);
                });
            },
            subtitles: function(data) {
                pandora.UI.set({videoSubtitles: data.subtitles});
            },
            timeline: function(data) {
                updateSmallTimelineURL();
                pandora.UI.set({videoTimeline: data.timeline});
            },
            toggleclips: function(data) {
                pandora.UI.set({showClips: data.showClips});
            },
            toggletimeline: function(data) {
                pandora.UI.set({showTimeline: data.showTimeline});
            },
            view: function(data) {
                pandora.UI.set({editView: data.view});
                data.view == 'grid' && enableDragAndDrop();
            },
            volume: function(data) {
                pandora.UI.set({videoVolume: data.volume});
            },
            pandora_editview: function(data) {
                that.options({clipView: data.value});
            },
            pandora_editselection: function(data) {
                that.options({selected: data.value});
            },
            pandora_showclips: function(data) {
                that.options({showClips: data.value});
            },
            pandora_showtimeline: function(data) {
                that.options({showTimeline: data.value});
            },
            pandora_videotimeline: function(data) {
                that.options({timeline: data.value});
            }
        });
        that.updatePanel = function(callback) {
            Ox.Request.clearCache('getEdit');
            Ox.Request.clearCache('sortClips');
            getEdit(function() {
                updateClips();
                callback && callback();
            });
        };
        // FIXME: replaceElement resets inner collapsed state
        var right = that.css('right');
        pandora.$ui.mainPanel.replaceElement(1, that);
        that.css('right', right);

        updateSmallTimelineURL();
        editSettings.view == 'grid' && enableDragAndDrop();
        if (!Ox.Focus.focusedElementIsInput()) {
            that.gainFocus();
        }
    }

    function renderEdits() {
        that.css({
            'overflow-y': 'auto'
        });
        Ox.Bar({size: 24}).appendTo(that);
        var $content = Ox.Element()
                .css({padding: '16px'})
                .appendTo(that),
            isEditable = pandora.hasCapability('canEditSitePages');
        Ox.EditableContent({
                editable: false,
                value: Ox._('{0} Edits', [pandora.site.site.name]),
            })
            .css({
                height: '32px',
                fontSize: '18px',
            })
            .appendTo($content);
        Ox.Element()
            .css({height: '16px'})
            .appendTo($content);
        pandora.api.getPage({name: 'edits'}, function(result) {
            Ox.EditableContent({
                    clickLink: pandora.clickLink,
                    editable: isEditable,
                    tooltip: isEditable ? pandora.getEditTooltip() : '',
                    type: 'textarea',
                    placeholder: isEditable ? Ox._('Doubleclick to insert text') : '',
                    value: result.data.text
                })
                .css({
                    width: '100%'
                })
                .bindEvent({
                    submit: function(data) {
                        Ox.Request.clearCache('getPage');
                        pandora.api.editPage({
                            name: 'edits',
                            text: data.value
                        });
                    }
                })
                .appendTo($content);
        });
    }

    function renderEmbedEdit() {
        var editSettings = ui.edits[ui.edit] || pandora.site.editSettings
        that = Ox.VideoPlayer({
            clickLink: pandora.clickLink,
            clipRatio: pandora.site.video.previewRatio,
            clips: Ox.clone(edit.clips),
            clipTooltip: 'clips <span class="OxBright">' + Ox.SYMBOLS.shift + 'C</span>',
            clipView: editSettings.view,
            controlsBottom: [
                'play', 'volume', 'scale', 'timeline', 'position', 'settings'
            ],
            controlsTooltips: {
                close: Ox._('Close'),
                open: Ox._('Watch on {0}', [pandora.site.site.name])
            },
            controlsTop: [
                Ox.Fullscreen.available ? 'fullscreen' : 'space16'
            ].concat(
                ['chapterTitle', 'open']
            ),
            chapters: edit.clips.map(function(clip) {
                return {
                    position: clip.position,
                    title: pandora.getItemTitle(clip)
                };
            }),
            duration: edit.duration,
            enableFullscreen: Ox.Fullscreen.available,
            enableKeyboard: true,
            enableMouse: true,
            enablePosition: true,
            enableSubtitles: ui.videoSubtitles,
            enableTimeline: true,
            enableVolume: true,
            height: Ox.$document.height(),
            paused: true,
            showIconOnLoad: true,
            subtitles: getSubtitles(edit.clips),
            subtitlesDefaultTrack: Ox.getLanguageNameByCode(pandora.site.language),
            subtitlesTrack: Ox.getLanguageNameByCode(pandora.site.language),
            timeline: getSmallTimelineURL(),
            video: getVideos(),
            volume: ui.videoVolume,
            width: Ox.$document.width()
        }).bindEvent({
            fullscreen: function(data) {
                Ox.Fullscreen.toggle();
                setTimeout(that.resizePanel, 100);
            },
            open: function(data) {
                that.options({paused: true});
                var clip = Ox.last(edit.clips.filter(function(clip) {
                        return clip.position <= that.options('position');
                    })),
                    position = clip['in'] + that.options('position') - clip['position'],
                    url = document.location.protocol + '//'
                        + document.location.hostname + '/'
                        + clip.item + '/'
                        + Ox.formatDuration(position) + ','
                        + Ox.formatDuration(clip['in']) + ','
                        + Ox.formatDuration(clip.out);
                window.open(url, '_blank');
            },
        });
        pandora.$ui.embedPanel.replaceWith(that);
        pandora.$ui.embedPanel = that;
        updateSmallTimelineURL();
        Ox.$parent.postMessage('loaded');
    }

    function orderClips(ids) {
        edit.clips.forEach(function(clip) {
            clip.index = ids.indexOf(clip.id);
        });
        updateClips(Ox.sortBy(edit.clips, 'index'));
    }

    function getLayers(clips) {
        var layers = [];
        pandora.site.layers.forEach(function(layer, i) { 
            layers[i] = Ox.extend({}, layer, {
                title: Ox._(layer.title),
                item: Ox._(layer.item),
                items: Ox.flatten(clips.map(function(clip) {
                    return clip.layers[layer.id].map(function(annotation) {
                        var a = Ox.clone(annotation);
                        a['id'] = clip['id'] + '/' + a['id'];
                        a['in'] = Math.max(
                            clip['position'],
                            a['in'] - clip['in'] + clip['position']
                        );
                        a.out = Math.min(
                            clip['position'] + clip['duration'],
                            a.out - clip['in'] + clip['position']
                        );
                        return a;
                    });
                })),
            });
        });
        return layers;
    }

    function getSubtitles(clips) {
        var subtitles = [],
            subtitlesLayer = pandora.getSubtitlesLayer();
        subtitlesLayer && clips.map(function(clip) {
            if (clip.layers[subtitlesLayer]) {
                clip.layers[subtitlesLayer].forEach(function(subtitle) {
                    subtitles.push({
                        id: subtitle.id,
                        'in': Math.max(
                            clip['position'],
                            subtitle['in'] - clip['in'] + clip['position']
                        ),
                        out: Math.min(
                            clip['position'] + clip['duration'],
                            subtitle.out - clip['in'] + clip['position']
                        ),
                        text: subtitle.value.replace(/\n/g, ' ').replace(/<br\/?>/g, '\n')
                    });
                });
            }
        });
        return subtitles;
    }

    function serializeClips(clips) {
        // can be ids or clips
        return clips.map(function(clip) {
            if (Ox.isString(clip)) {
                clip = Ox.getObjectById(edit.clips, clip);
            }
            return (
                clip.annotation || clip.item + '/' + clip['in'] + '-' + clip.out
            ) + '/' + (clip.id || '');
        });
    }

    function sortClips(callback) {
        var sort = pandora.user.ui.editSort,
            key = sort[0].key,
            index;
        if (key == 'position') {
            key = 'in';
        }
        if ([
            'id', 'index', 'in', 'out', 'duration',
            'title', 'director', 'year', 'videoRatio'
        ].indexOf(key) > -1) {
            sortBy(key);
            index = 0;
            edit.clips.forEach(function(clip) {
                clip.sort = index++;
                if (sort[0].operator == '-') {
                    clip.sort = -clip.sort;
                }
            });
            updateDuration();
            callback(edit.clips);
        } else {
            pandora.api.sortClips({
                edit: edit.id,
                sort: sort
            }, function(result) {
                edit.clips.forEach(function(clip) {
                    clip.sort = result.data.clips.indexOf(clip.id);
                    if (sort[0].operator == '-') {
                        clip.sort = -clip.sort;
                    }
                });
                sortBy('sort');
                updateDuration();
                callback(edit.clips);
            });
        }
        function sortBy(key) {
            edit.clips = Ox.sortBy(edit.clips, sort[0].operator + key);
        }
    }

    function updateDuration() {
        edit.duration = 0;
        edit.clips.forEach(function(clip) {
            clip.position = edit.duration;
            edit.duration += clip.duration;
        });
    }

    function updateClips(clips) {
        clips = clips || edit.clips;
        edit.clips = clips;
        updateDuration();
        that.options({
            clips: Ox.clone(edit.clips),
            duration: edit.duration,
            layers: getLayers(edit.clips),
            smallTimelineURL: getSmallTimelineURL(),
            subtitles: getSubtitles(edit.clips),
            video: getVideos()
        });
        updateSmallTimelineURL();
    }

    function updateSmallTimelineURL() {
        var canvas = getSmallTimelineCanvas(),
            context = canvas.getContext('2d'),
            fps = getSmallTimelineFPS(),
            timelineIteration = self.timelineIteration = Ox.uid();
        Ox.serialForEach(edit.clips, function(clip) {
            var callback = Ox.last(arguments);
            if (!clip.duration) {
                callback()
                return;
            }
            pandora[
                fps == 1 ? 'getSmallClipTimelineURL' : 'getLargeClipTimelineURL'
            ](clip.item, clip['in'], clip.out, ui.videoTimeline, function(url) {
                var image = Ox.$('<img>')
                    .on({
                        load: function() {
                            if (timelineIteration == self.timelineIteration) {
                                context.drawImage(image, Math.floor(clip.position * fps), 0);
                                that.options(isEmbed ? 'timeline' : 'smallTimelineURL',
                                    canvas.toDataURL());
                                callback();
                            } else {
                                callback(false);
                            }
                        }
                    })
                    .attr({
                        src: url
                    })[0];
            });
        });
    }
    return that;

};
