// vim: et:ts=4:sw=4:sts=4:ft=javascript
'use strict';
pandora.ui.mainPanel = function() {
    var that = Ox.SplitPanel({
            elements: [
                {
                    collapsible: true,
                    collapsed: !pandora.user.ui.showSidebar,
                    element: pandora.$ui.leftPanel = pandora.ui.leftPanel(),
                    resizable: true,
                    resize: [192, 256, 320, 384],
                    size: pandora.user.ui.sidebarSize,
                    tooltip: 'sidebar <span class="OxBright">'
                        + Ox.SYMBOLS.SHIFT + 'S</span>'
                },
                {
                    element: pandora.$ui.rightPanel = pandora.ui.rightPanel()
                }
            ],
            orientation: 'horizontal'
        })
        .bindEvent({
            pandora_find: function() {
                var previousUI = pandora.UI.getPrevious();
                Ox.Log('FIND', 'handled in mainPanel', previousUI.item, previousUI._list)
                if (!previousUI.item && pandora.user.ui._list == previousUI._list) {
                    if (['map', 'calendar'].indexOf(pandora.user.ui.listView) > -1) {
                        pandora.$ui.contentPanel.replaceElement(1,
                            pandora.ui.navigationView(pandora.user.ui.listView)
                        );
                    } else {
                        if (['clips', 'clip'].indexOf(pandora.user.ui.listView) > -1) {
                            pandora.$ui.list.options({find: pandora.user.ui.itemFind});
                        }
                        pandora.$ui.list.reloadList();
                    }
                    // FIXME: why is this being handled _here_?
                    pandora.user.ui._filterState.forEach(function(data, i) {
                        if (!Ox.isEqual(data.selected, previousUI._filterState[i].selected)) {
                            if (pandora.user.ui.showFilters) {
                                pandora.$ui.filters[i].options({selected: data.selected});
                            } else {
                                pandora.$ui.filters[i].options({_reload: true, selected: []});
                            }
                        }
                        if (!Ox.isEqual(data.find, previousUI._filterState[i].find)) {
                            if (pandora.user.ui.showFilters) {
                                pandora.$ui.filters[i].reloadList();
                            } else {
                                // we can call reloadList here, since the items function
                                // handles the hidden filters case without making requests
                                pandora.$ui.filters[i].options({_reload: true}).reloadList();
                            }
                        }
                    });
                } else {
                    that.replaceElement(1, pandora.$ui.rightPanel = pandora.ui.rightPanel());
                }
            },
            pandora_item: function(data) {
                if (!data.value || !data.previousValue) {
                    that.replaceElement(1, pandora.$ui.rightPanel = pandora.ui.rightPanel());
                }
            },
            pandora_showsidebar: function(data) {
                data.value == that.options('elements')[0].collapsed && that.toggle(0);
            }
        });
    return that;
};

