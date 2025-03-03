'use strict';

pandora.ui.folderBrowserBar = function(id, section) {
    section = section || pandora.user.ui.section;
    var ui = pandora.user.ui,
        folderItems = pandora.getFolderItems(section),
        folderItem = folderItems.slice(0, -1),
        that = Ox.Bar({
            size: 24
        });
    pandora.$ui.findListsElement[id] = Ox.FormElementGroup({
            elements: [
                pandora.$ui.findListsSelect[id] = Ox.Select({
                        items: [
                            {id: 'user', title: Ox._('Find: User')},
                            {id: 'name', title: Ox._('Find: {0}', [Ox._(folderItem)])}
                        ],
                        overlap: 'right',
                        type: 'image'
                    })
                    .bindEvent({
                        change: function(data) {
                            var key = data.value,
                                value = pandora.$ui.findListsInput[id].value();
                            value && updateList(key, value);
                            pandora.$ui.findListsInput[id].options({
                                placeholder: data.title
                            });
                        }
                    }),
                pandora.$ui.findListsInput[id] = Ox.Input({
                        changeOnKeypress: true,
                        clear: true,
                        placeholder: Ox._('Find: User'),
                        width: pandora.getFoldersWidth() - 24
                    })
                    .bindEvent({
                        change: function(data) {
                            var key = pandora.$ui.findListsSelect[id].value(),
                                value = data.value;
                            updateList(key, value);
                        }
                    })
            ]
        })
        .css({
            float: 'right',
            margin: '4px',
            align: 'right'
        })
        .appendTo(that);
    function updateList(key, value) {
        pandora.$ui.folderList[id].options({
            items: function(data, callback) {
                var query = id == 'favorite' ? {conditions: [
                    {key: 'status', value: 'public', operator: '='},
                    {key: 'user', value: pandora.user.username, operator: '!=='},
                    {key: key, value: value, operator: '='}
                ], operator: '&'} : {conditions: [
                    {key: 'status', value: 'private', operator: '!='},
                    {key: key, value: value, operator: '='}
                ], operator: '&'};
                return pandora.api['find' + folderItems](Ox.extend(data, {
                    query: query
                }), callback);
            }
        });
    }
    return that;
};

