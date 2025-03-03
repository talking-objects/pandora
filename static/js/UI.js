'use strict';

pandora.UI = (function() {

    var self = {}, that = {};

    self.previousUI = {};

    that.encode = function(val) {
        return val.replace(/\./g, '\\.');
    };

    that.getPrevious = function(key) {
        // fixme: probably unneeded by now
        return !key ? self.previousUI : self.previousUI[key];
    };

    that.reset = function() {
        pandora.api.resetUI({}, function() {
            pandora.user.ui = pandora.site.user.ui;
            pandora.user.ui._list = pandora.getListState(
                pandora.user.ui.find
            );
            pandora.user.ui._filterState = pandora.getFilterState(
                pandora.user.ui.find
            );
            pandora.user.ui._documentFilterState = pandora.getDocumentFilterState(
                pandora.user.ui.findDocuments
            );
            pandora.user.ui._findState = pandora.getFindState(
                pandora.user.ui.find
            );
            pandora.user.ui._collection = pandora.getCollectionState(
                pandora.user.ui.findDocuments
            );
            pandora.user.ui._findDocumentsState = pandora.getFindDocumentsState(
                pandora.user.ui.findDocuments
            );
            Ox.Theme(pandora.user.ui.theme);
            pandora.$ui.appPanel.reload();
        });
    };

    // sets pandora.user.ui.key to val
    // key foo.bar.baz sets pandora.user.ui.foo.bar.baz
    // val null removes a key
    that.set = function(/* {key: val}[, flag] or key, val[, flag] */) {

        var add = {},
            args,
            collection,
            collectionView,
            collectionSettings = pandora.site.collectionSettings,
            editSettings = pandora.site.editSettings,
            item,
            list,
            listSettings = pandora.site.listSettings,
            listView,
            set = {},
            textSettings = pandora.site.textSettings,
            trigger = {},
            triggerEvents;

        if (Ox.isObject(arguments[0])) {
            args = arguments[0];
            triggerEvents = Ox.isUndefined(arguments[1]) ? true : arguments[1];
        } else {
            args = Ox.makeObject([arguments[0], arguments[1]]);
            triggerEvents = Ox.isUndefined(arguments[2]) ? true : arguments[1];
        }

        Ox.Log('UI', 'SET', JSON.stringify(args));

        self.previousUI = Ox.clone(pandora.user.ui, true);
        self.previousUI._list = pandora.getListState(self.previousUI.find);

        if (args.section == 'texts') {
            trigger.section = args.section;
            trigger.text = args.text;
        } else if (args.section == 'edits') {
            trigger.section = args.section;
            trigger.edit = args.edit;
        } else if (pandora.user.ui.section == 'documents' || args.section == 'documents') {
            if ('findDocuments' in args) {
                // the challenge here is that find may change list,
                // and list may then change listSort and listView,
                // which we don't want to trigger, since find triggers
                // (values we put in add will be changed, but won't trigger)
                collection = pandora.getCollectionState(args.findDocuments);
                pandora.user.ui._collection = collection;
                pandora.user.ui._documentFilterState = pandora.getDocumentFilterState(args.findDocuments);
                pandora.user.ui._findDocumentsState = pandora.getFindDocumentsState(args.findDocuments);
                if (pandora.$ui.appPanel && !pandora.stayInItemView) {
                    // if we're not on page load, and if find isn't a context change
                    // caused by an edit, then switch from item view to list view
                    args['document'] = '';
                }
                if (collection != self.previousUI._collection) {
                    Ox.Log('UI', 'FIND HAS CHANGED COLLECTION', self.previousUI._collection, '>', collection);
                    // if find has changed collection
                    Ox.forEach(collectionSettings, function(collectionSetting, setting) {
                        // then for each setting that corresponds to a collection setting
                        if (!Ox.isUndefined(args[setting])) {
                            add[setting] = args[setting];
                        } else if (
                            !pandora.user.ui.collections[collection]
                            || Ox.isUndefined(pandora.user.ui.collections[collection][collectionSetting])
                        ) {
                            // either add the default setting
                            add[setting] = pandora.site.user.ui[setting];
                        } else {
                            // or the existing collection setting
                            add[setting] = pandora.user.ui.collections[collection][collectionSetting];
                        }
                    });
                }
            } else {
                collection = self.previousUI._collection;
            }
            if (!pandora.user.ui.collections[collection]) {
                add['collections.' + that.encode(collection)] = {};
            }
            Ox.forEach(collectionSettings, function(collectionSetting, setting) {
                // for each setting that corresponds to a collection setting
                // set that collection setting to
                var key = 'collections.' + that.encode(collection) + '.' + collectionSetting;
                if (setting in args) {
                    // the setting passed to UI.set
                    add[key] = args[setting];
                } else if (setting in add) {
                    // or the setting changed via find
                    add[key] = add[setting];
                } else if (!pandora.user.ui.collections[collection]) {
                    // or the default setting
                    add[key] = pandora.site.user.ui[setting];
                }
            });
            // set nested lisColumnWidth updates
            Ox.forEach(args, function(value, key) {
                if (Ox.startsWith(key, 'collectionColumnWidth.')) {
                    key = 'collections.' + that.encode(collection) + '.columnWidth.'
                        + key.slice('collectionColumnWidth.'.length);
                    if (!(key in add)) {
                        add[key] = value;
                    }
                }
            });

            if (args.document) {
                // when switching to an item, update list selection
                add['collectionSelection'] = [args.document];
                add['collections.' + that.encode(collection) + '.selection'] = [args.document];
            }
        } else {
            if ('find' in args) {
                // the challenge here is that find may change list,
                // and list may then change listSort and listView,
                // which we don't want to trigger, since find triggers
                // (values we put in add will be changed, but won't trigger)
                list = pandora.getListState(args.find);
                pandora.user.ui._list = list;
                pandora.user.ui._filterState = pandora.getFilterState(args.find);
                pandora.user.ui._findState = pandora.getFindState(args.find);
                if (pandora.$ui.appPanel && !pandora.stayInItemView) {
                    // if we're not on page load, and if find isn't a context change
                    // caused by an edit, then switch from item view to list view
                    args['item'] = '';
                }
                if (list != self.previousUI._list) {
                    Ox.Log('UI', 'FIND HAS CHANGED LIST')
                    // if find has changed list
                    Ox.forEach(listSettings, function(listSetting, setting) {
                        // then for each setting that corresponds to a list setting
                        if (!Ox.isUndefined(args[setting])) {
                            add[setting] = args[setting];
                        } else if (
                            !pandora.user.ui.lists[list]
                            || Ox.isUndefined(pandora.user.ui.lists[list][listSetting])
                        ) {
                            // either add the default setting
                            add[setting] = pandora.site.user.ui[setting];
                        } else {
                            // or the existing list setting
                            add[setting] = pandora.user.ui.lists[list][listSetting];
                        }
                    });
                }
                add.itemFind = pandora.getItemFind(args.find);
            } else {
                list = self.previousUI._list;
            }
            // it is important to check for find first, so that
            // if find changes list, list is correct here
            item = args.item || pandora.user.ui.item;
            listView = add.listView || args.listView;

            if (listView) {
                if (pandora.isClipView(listView)) {
                    // when switching to a clip view, clear list selection
                    // (but don't trigger an additional event)
                    add.listSelection = [];
                } else if (['text', 'position'].indexOf(
                    pandora.user.ui.listSort[0].key
                ) > -1) {
                    // when switching to a non-clip view, with a sort key
                    // that only exists in clip view, reset sort to default
                    args.listSort = pandora.site.user.ui.listSort;
                }
            }

            if (!pandora.user.ui.lists[list]) {
                add['lists.' + that.encode(list)] = {};
            }
            Ox.forEach(listSettings, function(listSetting, setting) {
                // for each setting that corresponds to a list setting
                // set that list setting to
                var key = 'lists.' + that.encode(list) + '.' + listSetting;
                if (setting in args) {
                    // the setting passed to UI.set
                    add[key] = args[setting];
                } else if (setting in add) {
                    // or the setting changed via find
                    add[key] = add[setting];
                } else if (!pandora.user.ui.lists[list]) {
                    // or the default setting
                    add[key] = pandora.site.user.ui[setting];
                }
            });
            // set nested lisColumnWidth updates
            Ox.forEach(args, function(value, key) {
                if (Ox.startsWith(key, 'listColumnWidth.')) {
                    key = 'lists.' + that.encode(list) + '.columnWidth.'
                        + key.slice('listColumnWidth.'.length);
                    if (!(key in add)) {
                        add[key] = value;
                    }
                }
            });

            if (args.item) {
                // when switching to an item, update list selection
                add['listSelection'] = [args.item];
                add['lists.' + that.encode(list) + '.selection'] = [args.item];
                if (
                    !args.itemView
                    && ['timeline', 'player', 'editor'].indexOf(
                        pandora.user.ui.itemView
                    ) > -1
                    && !pandora.user.ui.videoPoints[item]
                    && !args['videoPoints.' + item]
                ) {
                    // if the item view doesn't change, remains a video view,
                    // video points don't exist yet, and won't be set,
                    // add default video points
                    add['videoPoints.' + item] = {
                        annotation: '',
                        'in': 0,
                        out: 0,
                        position: 0
                    };
                }
                if (args['videoPoints.' + item] && (
                    !pandora.user.ui.item
                    || pandora.user.ui.itemView != 'editor'
                )) {
                    pandora._dontSelectResult = true;
                }
            }

            if (['timeline', 'player', 'editor'].indexOf(args.itemView) > -1) {
                // when switching to a video view, add it as default video view
                args.videoView = args.itemView;
                if (
                    !pandora.user.ui.videoPoints[item]
                    && !args['videoPoints.' + item]
                ) {
                    // if video points don't exist yet, and won't be set,
                    // add default video points
                    add['videoPoints.' + item] = {
                        annotation: '',
                        'in': 0,
                        out: 0,
                        position: 0
                    };
                }
            }
        }

        if (args.edit) {
            // add local edit settings
            if (!pandora.user.ui.edits[args.edit]) {
                add['edits.' + that.encode(args.edit)] = {};
            }
            Ox.forEach(editSettings, function(value, key) {
                var editsKey = 'edits.' + that.encode(args.edit) + '.' + key;
                add[editsKey] = editsKey in args ? args[editsKey]
                    : (pandora.user.ui.edits[args.edit] && !Ox.isUndefined(
                        pandora.user.ui.edits[args.edit][key]
                    )) ? pandora.user.ui.edits[args.edit][key]
                    : value;
            });
        }

        Ox.forEach({
            editSelection: 'selection',
            editSort: 'sort',
            editView: 'view'
        }, function(editSetting, setting) {
            var key = 'edits.' + that.encode(
                args.edit || pandora.user.ui.edit
            ) + '.' + editSetting;
            if (setting in args) {
                // add local edit setting
                add[key] = args[setting];
            } else if (setting in add) {
                // add local edit setting
                add[key] = add[setting];
            } else if (key in add) {
                // add global edit setting
                add[setting] = add[key];
            }
        });

        if (args.text) {
            add['texts.' + that.encode(args.text)] = Ox.map(textSettings, function(value, key) {
                var textsKey = 'texts.' + that.encode(args.text),
                    textsSubKey = textsKey + '.' + key;
                return textsKey in args && key in args[textsKey] ? args[textsKey][key]
                    : textsSubKey in args ? args[textSubKey]
                    : (pandora.user.ui.texts[args.text] && !Ox.isUndefined(
                        pandora.user.ui.texts[args.text][key]
                    )) ? pandora.user.ui.texts[args.text][key]
                    : value;
            });
        }

        // items in args trigger events, items in add do not
        [args, add].forEach(function(obj, isAdd) {
            Ox.forEach(obj, function(val, key) {
                // make sure to not split at escaped dots ('\.')
                var keys = key.replace(/\\\./g, '\n').split('.').map(function(key) {
                        return key.replace(/\n/g, '.')
                    }),
                    part,
                    ui = pandora.user.ui;
                while (keys.length > 1) {
                    part = part ? part + '.' + keys[0] : keys[0];
                    if (Ox.isUndefined(ui[keys[0]])) {
                        ui[keys[0]] = {};
                        set[part] = {};
                    }
                    ui = ui[keys.shift()];
                }
                if (!Ox.isEqual(ui[keys[0]], val)) {
                    if (val === null) {
                        delete ui[keys[0]];
                    } else {
                        ui[keys[0]] = val;
                    }
                    set[key] = val;
                    if (!isAdd) {
                        trigger[key] = val;
                    }
                }
            });
        });
        if (Ox.len(set) && !pandora.isEmbedURL() && !pandora.isPrintURL()) {
            pandora.api.setUI(set);
        }
        triggerEvents && Ox.forEach(trigger, function(val, key) {
            Ox.Log('UI', 'TRIGGER ', key, val);
            Ox.forEach(pandora.$ui, function($element) {
                if (Ox.UI.isElement($element)) {
                    $element.triggerEvent('pandora_' + key.toLowerCase(), {
                        value: val,
                        previousValue: self.previousUI[key]
                    });
                }
            });
        });

        pandora.URL.update(Object.keys(
            !pandora.$ui.appPanel ? args : trigger
        ));

    };

    return that;

}());

