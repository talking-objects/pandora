'use strict';

pandora.ui.item = function() {

    var isVideoView = [
            'timeline', 'player', 'editor'
        ].indexOf(pandora.user.ui.itemView) > -1,
        item = pandora.user.ui.item,
        that = Ox.Element(),
        videopointsEvent = 'pandora_videopoints.' + item.toLowerCase();

    pandora.api.get({
        id: pandora.user.ui.item,
        keys: isVideoView ? Ox.unique(pandora.VIDEO_OPTIONS_KEYS.concat(pandora.site.itemTitleKeys)) : []
    }, pandora.user.ui.itemView == 'info' && pandora.hasCapability('canEditMetadata') ? 0 : -1, function(result) {

        if (pandora.user.ui.item != item) {
            return;
        }

        if (result.status.code == 200) {
            // we want to cache the title in any way, so that after closing
            // a dialog and getting to this item, the title is correct
            var documentTitle = pandora.getWindowTitle(result.data);
            document.title = pandora.getPageTitle(document.location.pathname) || documentTitle;
        }

        pandora.$ui.itemTitle
            .options({title: '<b>' + pandora.getItemTitle(result.data, true) + '</b>'})
            .show();

        // fixme: layers have value, subtitles has text?
        isVideoView && Ox.extend(result.data, pandora.getVideoOptions(result.data));
        if (isVideoView && result.data.duration) {
            var videoPoints = pandora.user.ui.videoPoints[item], set = {};
            ['in', 'out', 'position'].forEach(point => {
                if (videoPoints && videoPoints[point] > result.data.duration) {
                    set[point] = result.data.duration;
                }
            })
            if (!Ox.isEmpty(set)) {
                pandora.UI.set('videoPoints.' + item, Ox.extend(videoPoints[point], set[point]))
            }
        }

        if (!result.data.rendered && [
            'clips', 'timeline', 'player', 'editor', 'map', 'calendar'
        ].indexOf(pandora.user.ui.itemView) > -1) {
            var html = Ox._('Sorry, <i>{0}</i>'
                + ' currently doesn\'t have '
                + (['a', 'e', 'i', 'o'].indexOf(
                    pandora.user.ui.itemView.slice(0, 1)
                ) > -1 ? 'an': 'a') + ' '
                +'{1} view.', [result.data.title, Ox._(pandora.user.ui.itemView)]);

            var note = Ox.Element()
                .css({marginTop: '32px', fontSize: '12px', textAlign: 'center'})
            pandora.$ui.contentPanel.replaceElement(1, note);
            if (pandora.user.username == result.data.user || pandora.hasCapability('canSeeAllTasks')) {
                pandora.api.getTasks({
                    user: pandora.hasCapability('canSeeAllTasks') ? '' : pandora.user.username
                }, function(result_) {
                    var tasks = result_.data.items.filter(function(task) { return task.item == item})
                    if (tasks.length > 0) {
                        html = Ox._(
                            '<i>{0}</i> is currently processed. '
                            + '{1} view will be available in a moment.',
                            [result.data.title, Ox._(pandora.user.ui.itemView)]
                        )
                    }
                    note.html(html)
                })
            } else {
                note.html(html)
            }

            pandora.site.itemViews.filter(function(view) {
                return view.id == 'documents';
            }).length && pandora.api.get({
                id: pandora.user.ui.item,
                keys: ['numberofdocuments']
            }, function(result) {
                if (result.data.numberofdocuments) {
                    var $text = Ox.Element()
                        .css({marginTop: '32px', fontSize: '12px', textAlign: 'center'})
                        .html(
                            html
                            + '<br>'
                            + Ox._('There {0} <a href="{1}">{2}</a>', [
                                (result.data.numberofdocuments == 1 ? 'is' : 'are'),
                                '/' + pandora.user.ui.item + '/documents',
                                Ox.formatCount(result.data.numberofdocuments, 'document')
                            ])
                        )
                    pandora.$ui.contentPanel.replaceElement(1, $text);
                    pandora.createLinks($text);
                }
            });
            result.data.parts > 0 && pandora.updateStatus(pandora.user.ui.item);
        } else if (pandora.user.ui.itemView == 'info') {
            
            pandora.$ui.contentPanel.replaceElement(1,
                pandora.$ui.item = pandora.ui.infoView(result.data)
                    .bindEvent({
                        resize: function() {
                            pandora.$ui.item.resizeElement && pandora.$ui.item.resizeElement();
                        }
                    })
            );
            !result.data.rendered && result.data.parts > 0 && pandora.updateStatus(pandora.user.ui.item);
        
        } else if (pandora.user.ui.itemView == 'documents') {

            pandora.$ui.contentPanel.replaceElement(1,
                pandora.$ui.documents = pandora.ui.documentsPanel({
                    editable: result.data.editable,
                    isItemView: true
                })
            );

        } else if (pandora.user.ui.itemView == 'player') {

            pandora.$ui.contentPanel.replaceElement(1,
                pandora.$ui.player = pandora.ui.player(result.data)
            );

        } else if (pandora.user.ui.itemView == 'editor') {

            pandora.$ui.contentPanel.replaceElement(1,
                pandora.$ui.editor = pandora.ui.editor(result.data)
            );

        } else if (pandora.user.ui.itemView == 'timeline') {

            pandora.$ui.contentPanel.replaceElement(1,
                pandora.$ui.timeline = pandora.ui.timeline(result.data)
            );

        } else if (pandora.user.ui.itemView == 'clips') {

            pandora.$ui.contentPanel.replaceElement(1,
                pandora.ui.clipsView(result.data.videoRatio)
            );

        } else if (pandora.user.ui.itemView == 'map') {

            pandora.$ui.contentPanel.replaceElement(1,
                pandora.ui.navigationView('map', result.data.videoRatio)
            );

        } else if (pandora.user.ui.itemView == 'calendar') {

            pandora.$ui.contentPanel.replaceElement(1,
                pandora.ui.navigationView('calendar', result.data.videoRatio)
            );

        } else if (pandora.user.ui.itemView == 'data') {

            pandora.$ui.item = Ox.TreeList({
                data: result.data,
                width: pandora.$ui.mainPanel.size(1) - Ox.UI.SCROLLBAR_SIZE
            });
            pandora.$ui.contentPanel.replaceElement(1,
                Ox.Container().append(pandora.$ui.item)
            );

        } else if (pandora.user.ui.itemView == 'media') {

            pandora.$ui.contentPanel.replaceElement(1,
                pandora.$ui.item = pandora.ui.mediaView(result.data)
            );

        } else if (pandora.user.ui.itemView == 'frames' || pandora.user.ui.itemView == 'posters') {

            pandora.$ui.contentPanel.replaceElement(1,
                pandora.$ui.item = pandora.ui.PostersView().bindEvent({
                    resize: function() {
                        pandora.$ui.item.resizeElement();
                    }
                })
            );

        }

        if (isVideoView && result.data.rendered) {
            // handle links in annotations
            pandora.$ui[pandora.user.ui.itemView].bindEvent(
                videopointsEvent,
                function(data, event, element) {
                    var options = {};
                    if (pandora.user.ui.item && event == videopointsEvent) {
                        //Ox.print('DATA.VALUE', JSON.stringify(data.value));
                        if (data && data.value && data.value.annotation) {
                            options.selected = pandora.user.ui.item + '/' + data.value.annotation;
                        } else {
                            // if annotation got set to something other than '',
                            // points and position will be set in consequence,
                            // so lets try to keep events from looping
                            ['annotation', 'in', 'out', 'position'].forEach(function(key) {
                                if (!Ox.isUndefined(data.value[key])) {
                                    options[key == 'annotation' ? 'selected' : key] = data.value[key];
                                }
                            });
                        }
                        pandora.$ui[pandora.user.ui.itemView].options(options);
                    }
                }
            );
        }

    });

    return that;

};

