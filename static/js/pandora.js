// vim: et:ts=4:sw=4:sts=4:ft=javascript
/***
    Pandora
***/

// fixme: never set pandora.ui.videoPosition to 0 ... set to null a.k.a. delete
// fixme: sort=-director doesn't work
// fixme: don't reload full right panel on sortSelect
// fixme: clear items cache after login/logout

Ox.load({
    UI: {
        debug: true,
        hideScreen: false,
        loadImages: true,
        showScreen: true,
        theme: 'modern'
    },
    Geo: {}
}, function(browserSupported) {

// fixme: use Ox.extend()

    window.pandora = new Ox.App({url: '/api/'}).bindEvent({

        load: function(data) {

            if (!browserSupported) {
                return;
            }

            Ox.extend(pandora, {
                requests: {},
                ui: {}
            });

            loadResources('/static/json/pandora.json', function() {

                Ox.print('Ox.App load', data);

                // Ox.UI.hideLoadingScreen();

                Ox.extend(pandora, {
                    $ui: {
                        body: $('body'),
                        document: $(document),
                        window: $(window)
                            .resize(resizeWindow)
                            .unload(unloadWindow)
                    },
                    site: data.site,
                    user: data.user.level == 'guest' ? Ox.clone(data.site.user) : data.user
                });

                Ox.extend(pandora.site, {
                    clipKeys: Ox.map(data.site.clipKeys, function(key) {
                        return Ox.extend(key, {
                            operator: pandora._getSortOperator(key.type)
                        });
                    }),
                    findKeys: Ox.map(data.site.itemKeys, function(key) {
                        return key.find ? key : null;
                    }),
                    sectionFolders: {
                        items: [
                            {id: 'personal', title: 'Personal Lists'},
                            {id: 'favorite', title: 'Favorite Lists', showBrowser: false},
                            {id: 'featured', title: 'Featured Lists', showBrowser: false},
                            {id: 'volumes', title: 'Local Volumes'}
                        ],
                        edits: [
                            {id: 'personal', title: 'Personal Edits'},
                            {id: 'favorite', title: 'Favorite Edits', showBrowser: false},
                            {id: 'featured', title: 'Featured Edits', showBrowser: false}                        
                        ],
                        texts: [
                            {id: 'personal', title: 'Personal Texts'},
                            {id: 'favorite', title: 'Favorite Texts', showBrowser: false},
                            {id: 'featured', title: 'Featured Texts', showBrowser: false}                        
                        ] 
                    },
                    sortKeys: Ox.map(data.site.itemKeys, function(key) {
                        return key.columnWidth ? Ox.extend(key, {
                            operator: pandora._getSortOperator(key.type)
                        }) : null;
                    })
                });
                Ox.extend(pandora.user, {
                    sectionElement: 'buttons',
                    selectedMovies: [],
                    videoFormat: Ox.UI.getVideoFormat(pandora.site.video.formats)
                });
                // fixme: this should not happen
                if (!pandora.user.ui.lists[pandora.user.ui.list]) {
                    Ox.print('THIS SHOULD NOT HAPPEN', pandora.site.user.ui.lists[''])
                    pandora.user.ui.lists[pandora.user.ui.list] = pandora.site.user.ui.lists[''];
                }

                if (data.user.level == 'guest' && $.browser.mozilla) {
                    pandora.user.ui.theme = 'classic';
                }

                window.onpopstate = function(event) {
                    pandora.URL.update();
                };

                // set up url controller

                var itemsName = pandora.site.itemName.plural.toLowerCase(),
                    sortKeys = {}, spanType = {}, views = {};
                views[itemsName] = {
                    list: Ox.merge(
                        // 'grid' is the default view
                        ['grid'],
                        Ox.map(pandora.site.listViews, function(view) {
                            return view.id == 'grid' ? null : view.id;
                        })
                    ),
                    item: Ox.merge(
                        // 'info' is the default view, pandora.user.ui.videoView
                        // is the default view if there is a duration
                        ['info', pandora.user.ui.videoView],
                        pandora.site.itemViews.map(function(view) {
                            return [
                                'info', pandora.user.ui.videoView
                            ].indexOf(view.id) > -1 ? null : view.id;
                        })
                    )
                };
                sortKeys[itemsName] = {list: {}, item: {}};
                views[itemsName].list.forEach(function(view) {
                    sortKeys[itemsName].list[view] = Ox.merge(
                        pandora.isClipView(view) ? Ox.clone(pandora.site.clipKeys) : [],
                        // 'director' is the default sort key
                        [Ox.getObjectById(pandora.site.sortKeys, 'director')],
                        Ox.map(pandora.site.sortKeys, function(key) {
                            return key.id == 'director' ? null : key;
                        })
                    );
                });
                views[itemsName].item.forEach(function(view) {
                    if (pandora.isClipView(view, true)) {
                        sortKeys[itemsName].item[view] = Ox.merge(
                            // 'clip:position' is the default sort key
                            [Ox.getObjectById(pandora.site.clipKeys, 'clip:position')],
                            Ox.map(pandora.site.clipKeys, function(key) {
                                return key.id == 'clip:position' ? null : key;
                            })
                        );
                    }
                });
                spanType[itemsName] = {
                    list: {
                        map: 'location',
                        calendar: 'date'
                    },
                    item: {
                        video: 'duration',
                        timeline: 'duration',
                        map: 'location',
                        calendar: 'date'
                    }
                };
                                
                pandora._URL = Ox.URL({
                    findKeys: pandora.site.findKeys,
                    getItem: pandora.getItemByIdOrTitle,
                    getSpan: pandora.getMetadataByIdOrName,
                    pages: [
                        'about', 'contact', 'faq', 'help', 'home', 'news',
                        'preferences', 'signin', 'signout', 'signup',
                        'software', 'terms', 'tour'
                    ],
                    sortKeys: sortKeys,
                    spanType: spanType,
                    types: [pandora.site.itemName.plural.toLowerCase(), 'edits', 'texts'],
                    views: views
                });

                pandora.URL.parse(function() {

                    Ox.UI.hideLoadingScreen();

                    Ox.Theme(pandora.user.ui.theme);
                    pandora.$ui.appPanel = pandora.ui.appPanel().display();        

                    Ox.Request.requests() && pandora.$ui.loadingIcon.start();
                    pandora.$ui.body.ajaxStart(pandora.$ui.loadingIcon.start);
                    pandora.$ui.body.ajaxStop(pandora.$ui.loadingIcon.stop);

                    pandora.site.sectionButtonsWidth = pandora.$ui.sectionButtons.width() + 8;
                    
                });

            }, '/static/'); // fixme: why does loadResources have an argument after callback????
        }
    });

    function loadResources(json, callback, prefix) {
        prefix = prefix || '';
        $.getJSON(json, function(files) {
            var promises = [];
            files.forEach(function(file) {
                // fixme: opera doesnt fire onload for svg
                // fixme: we don't have any svgs, right?
                if ($.browser.opera && Ox.endsWith(file, '.svg')) {
                    return;
                }
                var dfd = new $.Deferred();
                promises.push(dfd.promise());
                Ox.loadFile(prefix + file, function() {
                    dfd.resolve();
                });
            });
            $.when.apply(null, promises)
                .done(function() {
                    callback();
                })
                .fail(function() {
                    throw new Error('File not found.')
                });
        });            
    }

    function resizeWindow() {
        pandora.resizeFolders();
        pandora.$ui.leftPanel.size(2, pandora.getInfoHeight());
        pandora.$ui.info.resizeInfo();
        if (!pandora.user.ui.item) {
            pandora.$ui.list.size();
            pandora.resizeGroups(pandora.$ui.rightPanel.width());
            if (pandora.user.ui.listView == 'map') {
                pandora.$ui.map.resize();
            }
        } else {
            //Ox.print('pandora.$ui.window.resize');
            pandora.$ui.browser.scrollToSelection();
            pandora.user.ui.itemView == 'info' && pandora.$ui.item.resize();
            pandora.user.ui.itemView == 'player' && pandora.$ui.player.options({
                // fixme: duplicated
                height: pandora.$ui.contentPanel.size(1),
                width: pandora.$ui.document.width() - pandora.$ui.mainPanel.size(0) - 1
            });
            pandora.user.ui.itemView == 'timeline' && pandora.$ui.editor.options({
                // fixme: duplicated
                height: pandora.$ui.contentPanel.size(1),
                width: pandora.$ui.document.width() - pandora.$ui.mainPanel.size(0) - 1
            });
        }
    }

    function unloadWindow() {
        // fixme: ajax request has to have async set to false for this to work
        pandora.user.ui.section == 'items' &&
            ['player', 'timeline'].indexOf(pandora.user.ui.itemView) > -1 &&
            pandora.user.ui.item &&
            pandora.UI.set(
                'videoPosition|' + pandora.user.ui.item,
                pandora.$ui[
                    pandora.user.ui.itemView == 'player' ? 'player' : 'editor'
                ].options('position')
            );
    }

});
