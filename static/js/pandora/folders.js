// vim: et:ts=4:sw=4:sts=4:ft=javascript
'use strict';
pandora.ui.folders = function() {
    var ui = pandora.user.ui,
        counter = 0,
        that = Ox.Element()
            .css({overflowX: 'hidden', overflowY: 'auto'})
            .bindEvent({
                resize: pandora.resizeFolders
            }),
        folderItems = ui.section == 'items' ? 'Lists' : Ox.toTitleCase(ui.section),
        folderItem = folderItems.slice(0, -1);
    //var $sections = [];

    pandora.$ui.allItems = pandora.ui.allItems().appendTo(that);
    pandora.$ui.folder = [];
    pandora.$ui.folderBrowser = {};
    pandora.$ui.folderList = {};
    pandora.$ui.findListElement = {};
    pandora.$ui.findListSelect = {};
    pandora.$ui.findListInput = {};
    pandora.$ui.manageListsButton = {};
    pandora.site.sectionFolders[ui.section].forEach(function(folder, i) {
        var extras, $select;
        if (folder.id == 'personal') {
            if (pandora.user.level == 'guest') {
                extras = [
                    infoButton('Personal ' + folderItems, 'To create and share your own ' + (ui.section == 'items'
                        ? 'lists of ' + pandora.site.itemName.plural.toLowerCase()
                        : ui.section) + ', please sign up or sign in.')
                ];
            } else {
                if (ui.section == 'items') {
                    extras = [
                        pandora.$ui.personalListsMenu = Ox.MenuButton({
                            items: [
                                { id: 'newlist', title: 'New List' },
                                { id: 'newlistfromselection', title: 'New List from Selection', disabled: ui.listSelection.length == 0 },
                                { id: 'newsmartlist', title: 'New Smart List' },
                                { id: 'newsmartlistfromresults', title: 'New Smart List from Results' },
                                {},
                                { id: 'duplicatelist', title: 'Duplicate Selected List', disabled: !pandora.user.ui._list },
                                { id: 'editlist', title: 'Edit Selected List...', disabled: !pandora.user.ui._list },
                                { id: 'deletelist', title: 'Delete Selected List...', disabled: !pandora.user.ui._list }
                            ],
                            title: 'edit',
                            tooltip: 'Manage Personal Lists',
                            type: 'image'
                        })
                        .bindEvent({
                            click: function(data) {
                                var $list = pandora.$ui.folderList[folder.id];
                                // fixme: duplicated
                                if ([
                                    'newlist', 'newlistfromselection', 'newsmartlist', 'newsmartlistfromresults'
                                ].indexOf(data.id) > -1) {
                                    pandora.addList(data.id.indexOf('smart') > -1, data.id.indexOf('from') > -1);
                                } else if (data.id == 'duplicatelist') {
                                    pandora.addList(pandora.user.ui._list);
                                } else if (data.id == 'editlist') {
                                    pandora.ui.listDialog().open();
                                } else if (data.id == 'deletelist') {
                                    pandora.ui.deleteListDialog().open();
                                }
                            },
                            pandora_find: function() {
                                var action = ui._list
                                    && pandora.getListData(ui._list).user == pandora.user.username
                                    ? 'enableItem' : 'disableItem';
                                // fixme: duplicated
                                pandora.$ui.personalListsMenu[action]('editlist');
                                pandora.$ui.personalListsMenu[action]('duplicatelist');
                                pandora.$ui.personalListsMenu[action]('deletelist');
                                pandora.$ui.personalListsMenu[
                                    ui.listSelection.length ? 'enableItem' : 'disableItem'
                                ]('newlistfromselection');
                            },
                            pandora_listselection: function(data) {
                                pandora.$ui.personalListsMenu[
                                    data.value.length ? 'enableItem' : 'disableItem'
                                ]('newlistfromselection');
                            }
                        })
                    ];
                } else if(ui.section == 'texts') {
                    extras = [
                        pandora.$ui.personalListsMenu = Ox.MenuButton({
                            items: [
                                { id: 'newtext', title: 'New Text' },
                                { id: 'newpdf', title: 'New  PDF' },
                                {},
                                { id: 'deletetext', title: 'Delete Selected Text...', disabled: !ui.text }
                            ],
                            title: 'edit',
                            tooltip: 'Manage Personal Texts',
                            type: 'image'
                        })
                        .bindEvent({
                            click: function(data) {
                                var $list = pandora.$ui.folderList[folder.id];
                                if (data.id == 'newtext') {
                                    pandora.addText({type: 'text'});
                                } else if (data.id == 'newpdf') {
                                    pandora.addText({type: 'pdf'});
                                } else if (data.id == 'deletetext') {
                                    pandora.ui.deleteListDialog().open();
                                }
                            }
                        })
                        .bindEvent('pandora_text', function(data) {
                            pandora.$ui.personalListsMenu[
                                data.value && data.value.length ? 'enableItem' : 'disableItem'
                            ]('deletetext');
                        })
                    ];
                } else {
                    extras = [];
                }
            }
        } else if (folder.id == 'favorite') {
            if (pandora.user.level == 'guest') {
                extras = [infoButton('Favorite ' + folderItems,
                    'To browse and subscribe to shared ' + folderItems.toLowerCase() + ' from other users, please sign up or sign in.')];
            } else {
                extras = [pandora.$ui.manageListsButton['favorite'] = Ox.Button({
                    selectable: true,
                    style: 'symbol',
                    title: 'Edit',
                    tooltip: 'Manage Favorite ' + folderItems,
                    type: 'image'
                })
                .bindEvent({
                    change: function(data) {
                        var listData;
                        Ox.Request.clearCache(); // fixme: remove
                        pandora.site.sectionFolders[ui.section][i].showBrowser = !pandora.site.sectionFolders[ui.section][i].showBrowser;
                        if (pandora.site.sectionFolders[ui.section][i].showBrowser) {
                            pandora.$ui.folderList.favorite.replaceWith(
                                pandora.$ui.folderBrowser.favorite = pandora.ui.folderBrowser('favorite')
                            );
                        } else {
                            listData = pandora.getListData();
                            if (
                                pandora.$ui.folderList.favorite.options('selected').length
                                && !listData.subscribed
                            ) {
                                // the selected list in the favorites browser is not in the favorites folder
                                pandora.$ui.folderList.favorite.options({selected: []});
                                if (Ox.getObjectById(pandora.site.sectionFolders[ui.section], 'featured').showBrowser) {
                                    // but in the featured browser
                                    pandora.$ui.folderList.featured.options({selected: [listData.id]});
                                } else {
                                    // and nowhere else
                                    pandora.UI.set({
                                        find: pandora.site.user.ui.find
                                    });
                                }
                            }
                            pandora.$ui.folderBrowser.favorite.replaceWith(
                                pandora.$ui.folderList.favorite = pandora.ui.folderList('favorite')
                            );
                        }
                        pandora.resizeFolders();
                    }
                })];
            }
        } else if (folder.id == 'featured') {
            if (pandora.user.level != 'admin') {
                extras = [infoButton('Featured ' + folderItems, 'Featured ' + folderItems.toLowerCase() + ' are selected public ' + folderItems.toLowerCase() + ', picked by the ' + pandora.site.site.name + ' staff.')];
            } else {
                extras = [pandora.$ui.manageListsButton['featured'] = Ox.Button({
                    selectable: true,
                    style: 'symbol',
                    title: 'Edit',
                    tooltip: 'Manage Featured ' + folderItems,
                    type: 'image'
                })
                .bindEvent({
                    change: function(data) {
                        var listData;
                        Ox.Request.clearCache(); // fixme: remove
                        pandora.site.sectionFolders[ui.section][i].showBrowser = !pandora.site.sectionFolders[ui.section][i].showBrowser;
                        if (pandora.site.sectionFolders[ui.section][i].showBrowser) {
                            pandora.$ui.folderList.featured.replaceWith(
                                pandora.$ui.folderBrowser.featured = pandora.ui.folderBrowser('featured')
                            );
                        } else {
                            listData = pandora.getListData();
                            Ox.Log('', 'FEATURED', listData)
                            if (
                                pandora.$ui.folderList.featured.options('selected').length
                                && listData.status != 'featured'
                            ) {
                                // the selected list in the featured browser is not in the featured folder
                                pandora.$ui.folderList.featured.options({selected: []});
                                if (listData.user == pandora.user.username) {
                                    // but in the personal folder
                                    pandora.$ui.folderList.personal.options({selected: [listData.id]});
                                } else if (
                                    listData.subscribed
                                    || Ox.getObjectById(pandora.site.sectionFolders[ui.section], 'favorite').showBrowser
                                ) {
                                    // but in the favorites folder or browser
                                    pandora.$ui.folderList.favorite.options({selected: [listData.id]});
                                } else {
                                    // and nowhere else
                                    pandora.UI.set({
                                        find: pandora.site.user.ui.find
                                    });
                                }
                            }
                            pandora.$ui.folderBrowser.featured.replaceWith(
                                pandora.$ui.folderList.featured = pandora.ui.folderList('featured')
                            );
                        }
                        pandora.resizeFolders();
                    }
                })];
            }
        } else if (folder.id == 'volumes') {
            if (pandora.user.level == 'guest') {
                extras = [infoButton('Local Volumes', 'To import movies from a local disk, please sign up or sign in.')];
            } else {
                extras = [Ox.MenuButton({
                    items: [
                        { id: 'add', title: 'Add Volume...', disabled: true },
                        { id: 'scan', title: 'Scan Selected Volume...', disabled: true },
                        { id: 'remove', title: 'Remove Selected Volume...', disabled: true },
                        {},
                        { id: 'import', title: 'Import Movies...', disabled: true }
                    ],
                    title: 'edit',
                    tooltip: 'Manage Volumes',
                    type: 'image'
                })
                .bindEvent({
                    click: function(data) {
                    }
                })];
            }
        }
        pandora.$ui.folder[i] = Ox.CollapsePanel({
                id: folder.id,
                collapsed: !ui.showFolder.items[folder.id],
                extras: extras,
                size: 16,
                title: folder.title
            })
            .bindEvent({
                // fixme: duplicated
                click: function(data) {
                    var $list = pandora.$ui.folderList[i],
                        hasFocus, id;
                    if (data.id == 'new' || data.id == 'newsmart') {
                        pandora.api.addList({
                            name: 'Untitled',
                            status: 'private',
                            type: data.id == 'new' ? 'static' : 'smart'
                        }, function(result) {
                            id = result.data.id;
                            pandora.URL.set('?find=list:' + id)
                            Ox.Request.clearCache(); // fixme: remove
                            $list.reloadList().bindEventOnce({
                                load: function(data) {
                                    $list.gainFocus()
                                        .options({selected: [id]})
                                        .editCell(id, 'name');
                                }
                            });
                        });
                    } else if (data.id == 'browse') {
                        // alert('??')
                        /*
                        pandora.$ui.sectionList[1].replaceWith(pandora.$ui.publicLists = pandora.ui.publicLists());
                        pandora.site.showAllPublicLists = true;
                        */
                    }
                },
                toggle: function(data) {
                    data.collapsed && pandora.$ui.folderList[folder.id].loseFocus();
                    pandora.UI.set('showFolder.items.' + folder.id, !data.collapsed);
                    pandora.resizeFolders();
                }
            });
        //$sections.push(pandora.$ui.section[i]);
        pandora.$ui.folderList[folder.id] = pandora.ui.folderList(folder.id)
            .bindEvent({
                selectafter: function() {
                    // ...
                },
                selectbefore: function() {
                    // ...
                }
            })
            .bindEventOnce({
                init: function(data) {
                    if (++counter == pandora.site.sectionFolders[ui.section].length) {
                        pandora.$ui.folder.forEach(function($folder) {
                            that.append($folder);
                        });
                        pandora.resizeFolders();
                        pandora.selectList();
                    }
                }
            })
            .appendTo(pandora.$ui.folder[i].$content);
    });
    function infoButton(title, text) {
        return Ox.Button({
            style: 'symbol',
            title: 'info',
            type: 'image'
        }).bindEvent({
            click: function() {
                var $dialog = Ox.Dialog({
                    buttons: title != 'Featured Lists' ? [
                        Ox.Button({title: 'Sign Up...'}).bindEvent({
                            click: function() {
                                $dialog.close();
                                pandora.$ui.accountDialog = pandora.ui.accountDialog('signup').open();
                            }
                        }),
                        Ox.Button({title: 'Sign In...'}).bindEvent({
                            click: function() {
                                $dialog.close();
                                pandora.$ui.accountDialog = pandora.ui.accountDialog('signin').open();
                            }
                        }),
                        {},
                        Ox.Button({title: 'Not Now'}).bindEvent({
                            click: function() {
                                $dialog.close();
                            }
                        })
                    ] : [
                        Ox.Button({title: 'Close'}).bindEvent({
                            click: function() {
                                $dialog.close();
                            }
                        })
                    ],
                    content: Ox.Element()
                        .append(
                            $('<img>')
                                .attr({src: '/static/png/icon.png'})
                                .css({position: 'absolute', left: '16px', top: '16px', width: '64px', height: '64px'})
                        )
                        .append(
                            $('<div>')
                                .css({position: 'absolute', left: '96px', top: '16px', width: '192px'})
                                .html(text)
                        ),
                    fixedSize: true,
                    height: 128,
                    removeOnClose: true,
                    width: 304,
                    title: title
                }).open();
            }
        });
    }
    that.bindEvent({
        pandora_find: function() {
            var folder = pandora.getListData().folder,
                list = pandora.user.ui._list,
                previousList = pandora.UI.getPrevious()._list;
            if (list != previousList) {
                Ox.forEach(pandora.$ui.folderList, function($list, id) {
                    id != folder && $list.options('selected', []);
                });
                folder && pandora.$ui.folderList[folder].options({selected: [list]});
            }
            /*
            if (!pandora.user.ui._list && previousUI._list) {
                pandora.$ui.folderList[pandora.getListData(previous)]
                Ox.forEach(pandora.$ui.folderList, function($list) {
                    $list.options({selected: []});
                });
            }
            */
        },
        pandora_text: function() {
            if (!pandora.user.ui.text) {
                Ox.forEach(pandora.$ui.folderList, function($list, id) {
                    $list.options('selected', []);
                });
            }
        }
    })
    return that;
};
