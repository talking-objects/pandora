// vim: et:ts=4:sw=4:sts=4:ft=javascript

'use strict';

pandora.ui.documentFilterForm = function(options) {
    // mode can be find, collection, embed
    var collection = options.list,
        mode = options.mode,
        that = Ox.Element();

    if (mode == 'list') {
        mode = 'collection';
    }

    pandora.api.findCollections({
        query: {
            conditions: [{key: 'type', value: 'static', operator: '='}],
            operator: '&'
        },
        keys: ['id'],
        range: [0, 1000],
        sort: [{key: 'user', operator: '+'}, {key: 'name', operator: '+'}]
    }, function(result) {
        that.append(
            that.$filter = Ox.Filter({
                findKeys: pandora.site.documentKeys.map(function(documentKey) {
                    var key = Ox.clone(documentKey, true);
                    key.title = Ox._(key.title);
                    if (key.format && key.format.type == 'ColorPercent') {
                        key.format.type = 'percent';
                    }
                    Ox.print(key);
                    return key;
                }).concat([{
                    id: 'collection',
                    title: Ox._('Collection'),
                    type: 'list',
                    values: result.data.items.map(function(item) {
                        return item.id;
                    })
                }]),
                list: mode == 'find' ? {
                    sort: pandora.user.ui.collectionSort,
                    view: pandora.user.ui.collectionView
                } : null,
                sortKeys: pandora.site.documentSortKeys,
                value: Ox.clone(mode == 'collection' ? collection.query : pandora.user.ui.documentFind, true),
                viewKeys: pandora.site.collectionViews
            })
            .css(mode == 'embed' ? {} : {padding: '16px'})
            .bindEvent({
                change: function(data) {
                    if (mode == 'find') {
                        if (pandora.user.ui.updateAdvancedFindResults) {
                            that.updateResults();
                        }
                    } else if (mode == 'collection') {
                        pandora.api.editCollection({
                            id: collection.id,
                            query: data.value
                        }, function(result) {
                            if (pandora.user.ui.updateAdvancedFindResults) {
                                that.updateResults();
                            }
                        });
                    }
                    that.triggerEvent('change', data);
                }
            })
        );
        that.getList = that.$filter.getList;
        that.value = that.$filter.value;
    });
    that.updateResults = function() {
        if (mode == 'collection') {
            Ox.Request.clearCache(collection.id);
            pandora.$ui.list && pandora.$ui.list
                .bindEventOnce({
                    init: function(data) {
                        pandora.$ui.folderList[
                            pandora.getListData().folder
                        ].value(collection.id, 'query', that.$filter.options('value'));
                    }
                })
                .reloadList();
            /*
            pandora.$ui.filters && pandora.$ui.filters.forEach(function($filter) {
                $filter.reloadList();
            });
            */
        } else {
            pandora.UI.set({find: Ox.clone(that.$filter.options('value'), true)});
            pandora.$ui.findElement.updateElement();
        }
    };
    return that;
};

