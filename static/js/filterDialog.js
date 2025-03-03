'use strict';

pandora.ui.filterDialog = function() {

    var that = Ox.Dialog({
            buttons: [
                Ox.Button({
                        id: 'done',
                        title: Ox._('Done')
                    })
                    .bindEvent({
                        click: function() {
                            var list = pandora.$ui.filterForm.getList();
                            if (list.save) {
                                pandora.api[
                                    pandora.user.ui.section == 'documents' ? 'addCollection' : 'addList'
                                ]({
                                    name: list.name,
                                    query: list.query,
                                    status: 'private',
                                    type: 'smart'
                                }, function(result) {
                                    var $list = pandora.$ui.folderList.personal,
                                        id = result.data.id;
                                    if (pandora.user.ui.section) {
                                        pandora.UI.set({
                                            findDocuments: {
                                                conditions: [{key: 'collection', value: id, operator: '=='}],
                                                operator: '&'
                                            }
                                        });
                                    } else {
                                        pandora.UI.set({
                                            find: {
                                                conditions: [{key: 'list', value: id, operator: '=='}],
                                                operator: '&'
                                            }
                                        });
                                    }
                                    Ox.Request.clearCache(); // fixme: remove
                                    $list.bindEventOnce({
                                            load: function(data) {
                                                $list.gainFocus()
                                                    .options({selected: [id]});
                                            }
                                        })
                                        .reloadList();
                                });
                            } else if (!pandora.user.ui.updateAdvancedFindResults) {
                                pandora.$ui.filterForm.updateResults();
                            }
                            that.close();
                        }
                    })
            ],
            content: pandora.$ui.filterForm = (pandora.user.ui.section == 'documents'
                ? pandora.ui.documentFilterForm
                : pandora.ui.filterForm
            )({
                mode: 'find'
            }),
            maxWidth: 648 + Ox.UI.SCROLLBAR_SIZE,
            minHeight: 264,
            minWidth: 648 + Ox.UI.SCROLLBAR_SIZE,
            height: 264,
            // keys: {enter: 'save', escape: 'cancel'},
            removeOnClose: true,
            title: Ox._('Advanced Find'),
            width: 648 + Ox.UI.SCROLLBAR_SIZE
        }),

        $updateCheckbox = Ox.Checkbox({
                title: Ox._('Update Results in the Background'),
                value: pandora.user.ui.updateAdvancedFindResults
            })
            .css({float: 'left', margin: '4px'})
            .bindEvent({
                change: function(data) {
                    pandora.UI.set({updateAdvancedFindResults: data.value});
                    data.value && pandora.$ui.filterForm.updateResults();
                }
            });

    $($updateCheckbox.find('.OxButton')[0]).css({margin: 0});
    $(that.find('.OxBar')[1]).append($updateCheckbox);

    return that;

};

