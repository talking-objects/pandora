'use strict';

pandora.ui.player = function(data) {
    // FIXME: is this the right location to load subtitles?
    if (!data.subtitles) {
        data.subtitles = pandora.getSubtitles(data);
    }

    var ui = pandora.user.ui,

        that = Ox.VideoPlayerPanel({
            annotationsCalendarSize: ui.annotationsCalendarSize,
            annotationsMapSize: ui.annotationsMapSize,
            annotationsRange: ui.annotationsRange,
            annotationsSize: ui.annotationsSize,
            annotationsSort: ui.annotationsSort,
            annotationsTooltip: Ox._('annotations')
                + ' <span class="OxBright">' + Ox.SYMBOLS.shift + 'A</span>',
            audioTrack: data.audioTrack,
            censored: data.censored,
            censoredIcon: pandora.site.cantPlay.icon,
            censoredTooltip: Ox._(pandora.site.cantPlay.text),
            clickLink: pandora.clickLink,
            cuts: data.cuts || [],
            duration: data.duration,
            enableDownload: pandora.hasCapability('canDownloadVideo') >= data.rightslevel,
            enableSubtitles: ui.videoSubtitles,
            find: ui.itemFind,
            getLargeTimelineURL: function(type, i) {
                return pandora.getMediaURL(
                    '/' + ui.item + '/timeline' + type + '64p' + i + '.jpg?' + data.modified
                );
            },
            height: pandora.$ui.contentPanel.size(1),
            'in': ui.videoPoints[ui.item]['in'],
            itemName: pandora.site.itemName,
            layers: data.annotations,
            loop: ui.videoLoop,
            muted: ui.videoMuted,
            out: ui.videoPoints[ui.item].out,
            position: ui.videoPoints[ui.item].position,
            resolution: ui.videoResolution,
            scaleToFill: ui.videoScale == 'fill',
            selected: ui.videoPoints[ui.item].annotation
                ? ui.item + '/' + ui.videoPoints[ui.item].annotation
                : '',
            showAnnotations: ui.showAnnotations,
            showAnnotationsCalendar: ui.showAnnotationsCalendar,
            showAnnotationsMap: ui.showAnnotationsMap,
            showLayers: Ox.clone(ui.showLayers),
            showUsers: pandora.site.annotations.showUsers,
            showTimeline: ui.showTimeline,
            smallTimelineURL: pandora.getMediaURL('/' + ui.item + '/timeline16p.jpg?' + data.modified),
            subtitles: data.subtitles || [],
            subtitlesDefaultTrack: data.subtitlesDefaultTrack || Ox.getLanguageNameByCode(pandora.site.language),
            subtitlesLayer: data.subtitlesLayer,
            subtitlesOffset: ui.videoSubtitlesOffset,
            subtitlesTrack: data.subtitlesTrack || Ox.getLanguageNameByCode(pandora.site.language),
            timeline: ui.videoTimeline,
            timelineTooltip: Ox._('timeline') + ' <span class="OxBright">' + Ox.SYMBOLS.shift + 'T</span>',
            video: data.video,
            volume: ui.videoVolume,
            width: Ox.$document.width() - pandora.$ui.mainPanel.size(0) - 1
        }).bindEvent({
            annotationsrange: function(data) {
                pandora.UI.set({annotationsRange: data.range});
            },
            annotationssize: function(data) {
                pandora.UI.set({annotationsSize: data.size});
            },
            annotationssort: function(data) {
                pandora.UI.set({annotationsSort: data.sort});
            },
            censored: function() {
                that.options('fullscreen') && that.options({
                    fullscreen: false
                });
                pandora.URL.push(pandora.site.cantPlay.link);
            },
            copy: function(data) {
                pandora.clipboard.copy(data.map(function(clip) {
                    return clip.annotation || ui.item + '/' + clip['in'] + '-' + clip.out;
                }), 'clip');
            },
            copyadd: function(data) {
                pandora.clipboard.add(data.map(function(clip) {
                    return clip.annotation || ui.item + '/' + clip['in'] + '-' + clip.out;
                }), 'clip');
            },
            downloadvideo: function() {
                pandora.ui.downloadVideoDialog({
                    item: ui.item,
                    rightsLevel: data.rightsLevel,
                    source: data.source && pandora.hasCapability('canDownloadSource'),
                    title: data.title,
                    video: data.video
                }).open();
            },
            find: function(data) {
                pandora.UI.set({itemFind: data.find});
            },
            gainfocus: function() {
                pandora.$ui.mainMenu.replaceItemMenu();
            },
            info: function(data) {
                pandora.ui.annotationDialog(
                    Ox.getObjectById(pandora.site.layers, data.layer).title
                ).open();
            },
            loop: function(data) {
                pandora.UI.set({videoLoop: data.loop});
            },
            muted: function(data) {
                pandora.UI.set({videoMuted: data.muted});
            },
            playing: function(data) {
                pandora.UI.set(
                    'videoPoints.' + ui.item + '.position',
                    data.position
                );
            },
            points: function(data) {
                pandora.UI.set('videoPoints.' + ui.item, {
                    annotation: ui.videoPoints[ui.item].annotation,
                    'in': data['in'],
                    out: data.out,
                    position: data.position
                });
            },
            position: function(data) {
                pandora.UI.set(
                    'videoPoints.' + ui.item + '.position',
                    data.position
                );
            },
            resizeannotations: function(data) {
                pandora.UI.set({annotationsSize: data.annotationsSize});
            },
            resizecalendar: function(data) {
                pandora.UI.set({annotationsCalendarSize: data.size});
            },
            resizemap: function(data) {
                pandora.UI.set({annotationsMapSize: data.size});
            },
            resolution: function(data) {
                pandora.UI.set({videoResolution: data.resolution});
            },
            scale: function(data) {
                pandora.UI.set({videoScale: data.scale});
            },
            select: function(data) {
                pandora.UI.set('videoPoints.' + ui.item + '.annotation', data.id.split('/')[1] || '');
            },
            subtitles: function(data) {
                pandora.UI.set({videoSubtitles: data.subtitles});
            },
            toggleannotations: function(data) {
                pandora.UI.set({showAnnotations: data.showAnnotations});
            },
            togglelayer: function(data) {
                pandora.UI.set('showLayers.' + data.layer, !data.collapsed);
            },
            togglemap: function(data) {
                pandora.UI.set({showAnnotationsMap: !data.collapsed});
            },
            togglesize: function(data) {
                pandora.UI.set({videoSize: data.size});
            },
            toggletimeline: function(data) {
                pandora.UI.set({showTimeline: data.showTimeline});
            },
            volume: function(data) {
                pandora.UI.set({videoVolume: data.volume});
            },
            pandora_showannotations: function(data) {
                that.options({showAnnotations: data.value});
            },
            pandora_showtimeline: function(data) {
                that.options({showTimeline: data.value});
            },
            pandora_videotimeline: function(data) {
                that.options({timeline: data.value});
            }
        });

    return that;
  
};
