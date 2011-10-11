// vim: et:ts=4:sw=4:sts=4:ft=javascript

pandora.ui.eventsDialog = function() {
    var height = Math.round((window.innerHeight - 48) * 0.9),
        width = Math.round(window.innerWidth * 0.9),
        that = Ox.Dialog({
            buttons: [
                Ox.Button({
                    id: 'managePlaces',
                    title: 'Manage Places...'
                }).bindEvent({
                    click: function() {
                        // ...
                    }
                }),
                {},
                Ox.Button({
                    id: 'done',
                    title: 'Done',
                    width: 48
                }).bindEvent({
                    click: function() {
                        that.close();
                    }
                })
            ],
            closeButton: true,
            content: Ox.Element().append(
                $('<img>')
                    .attr({src: Ox.UI.getImageURL('symbolLoadingAnimated')})
                    .css({
                        position: 'absolute',
                        width: '32px',
                        height: '32px',
                        left: 0,
                        top: 0,
                        right: 0,
                        bottom: 0,
                        margin: 'auto'
                    })
            ),
            height: height,
            maximizeButton: true,
            minHeight: 256,
            minWidth: 512,
            padding: 0,
            title: 'Manage Events',
            width: width
        })
        .bindEvent({
            resize: function(data) {
                // setting width would cause an expensive calendar redraw
                $content && $content.options({height: data.height});
            },
            resizeend: function(data) {
                $content && $content.options(data);
            }
        }),
        $content;

    pandora.api.findEvents({
        query: {conditions: [], operator: '&'}        
    }, function(result) {
        pandora.api.findEvents({
            query: {conditions: [], operator: '&'},
            keys: [],
            range: [0, result.data.items],
            sort: [{key: 'name', operator: '+'}]
        }, function(result) {
            that.options({
                content: $content = Ox.ListCalendar({
                    addEvent: function(event, callback) {
                        pandora.api.addEvent(event, function(result) {
                            Ox.Request.clearCache(); // fixme: remove
                            callback(result);
                        });
                    },
                    editEvent: function(event, callback) {
                        pandora.api.editEvent(event, function(result) {
                            Ox.Request.clearCache(); // fixme: remove
                            callback(result);
                        });
                    },
                    events: result.data.items,
                    height: height - 48,
                    removeEvent: function(event, callback) {
                        pandora.api.removeEvent(event, function(result) {
                            Ox.Request.clearCache(); // fixme: remove
                            callback(result);
                        });
                    },
                    width: width
                })
            });
        })
    })

    return that;
};

