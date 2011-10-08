// vim: et:ts=4:sw=4:sts=4:ft=javascript
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

    // sets pandora.user.ui.key to val
    // key foo.bar.baz sets pandora.user.ui.foo.bar.baz
    // val null removes a key
    that.set = function(/* {key: val}[, flag] or key, val[, flag] */) {
        var add = {},
            args,
            doNotTriggerEvents,
            listSettings = pandora.site.listSettings,
            set = {},
            trigger = {};
        if (Ox.isObject(arguments[0])) {
            args = arguments[0];
            triggerEvents = Ox.isUndefined(arguments[1]) ? true : arguments[1];
        } else {
            args = Ox.makeObject([arguments[0], arguments[1]]);
            triggerEvents = Ox.isUndefined(arguments[2]) ? true : arguments[1];
        }
        Ox.print('UI SET', args)
        self.previousUI = Ox.clone(pandora.user.ui, true);
        Ox.forEach(args, function(val, key) {
            if (key == 'find') {
                // the challenge here is that find may change list,
                // and list may then change listSort and listView,
                // which we don't want to trigger, since find triggers
                var list = pandora.getListsState(val);
                add['item'] = '';
                pandora.user.ui._list = list;
                pandora.user.ui._groupsState = pandora.getGroupsState(val);
                pandora.user.ui._findState = pandora.getFindState(val);
                // make sure we don't do this on page load
                if (pandora.$ui.appPanel && list != self.previousUI._list) {
                    if (!pandora.user.ui.lists[list]) {
                        add['lists.' + that.encode(list)] = {};
                    }
                    Ox.forEach(listSettings, function(listSetting, setting) {
                        if (!pandora.user.ui.lists[list]) {
                            // add default list setting and copy to settings
                            add['lists.' + that.encode(list)][listSetting] = pandora.site.user.ui[setting];
                            add[setting] = pandora.site.user.ui[setting];
                        } else {
                            // copy lists setting to settings
                            add[setting] = pandora.user.ui.lists[list][listSetting]
                        }
                    });
                }
            } else if (Object.keys(listSettings).indexOf(key) > -1) {
                // copy setting to list setting
                add['lists.' + that.encode(pandora.user.ui._list || '') + '.' + listSettings[key]] = val;
            } else if (key == 'item' && val) {
                // when switching to an item, update list selection
                add['listSelection'] = [val];
                add['lists.' + that.encode(pandora.user.ui._list || '') + '.selection'] = [val];
            }
            if ((
                key == 'item'
                && ['video', 'timeline'].indexOf(pandora.user.ui.itemView) > -1
                && !pandora.user.ui.videoPoints[val]
                ) || (
                key == 'itemView'
                && ['video', 'timeline'].indexOf(val) > -1
                && !pandora.user.ui.videoPoints[pandora.user.ui.item]
            )) {
                // add default videoPoints
                add['videoPoints.' + (
                    key == 'item' ? val : pandora.user.ui.item
                )] = {'in': 0, out: 0, position: 0};
            }
        });
        [args, add].forEach(function(obj, isAdd) {
            Ox.forEach(obj, function(val, key) {
                var keys = key.replace(/([^\\])\./g, '$1\n').split('\n'),
                    ui = pandora.user.ui;
                while (keys.length > 1) {
                    ui = ui[keys.shift()];
                }
                if (!Ox.isEqual(ui[keys[0]], val)) {
                    if (val === null) {
                        delete ui[keys[0]]
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
        Ox.len(set) && pandora.api.setUI(set);
        triggerEvents && Ox.forEach(trigger, function(val, key) {
            Ox.forEach(pandora.$ui, function(element) {
                element.ox && element.triggerEvent('pandora_' + key.toLowerCase(), {
                    value: val,
                    previousValue: self.previousUI[key]
                });
            });
        });
        Ox.print('isBooting?', !pandora.$ui.appPanel, Object.keys(args), pandora.user.ui.listView);
        pandora.URL.update(Object.keys(
            !pandora.$ui.appPanel ? args : trigger
        ));
    };

    return that;

}());

