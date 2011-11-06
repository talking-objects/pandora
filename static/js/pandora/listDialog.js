// vim: et:ts=4:sw=4:sts=4:ft=javascript

'use strict';

pandora.ui.listDialog = function(section) {

    section = section || 'general';
    var width = getWidth(section);
    var listData = pandora.getListData(),
        tabs = Ox.merge([
            {id: 'general', title: 'General'},
            {id: 'icon', title: 'Icon'}
        ], listData.type == 'smart'
            ? [{id: 'query', title: 'Query'}]
            : []
        );
    Ox.getObjectById(tabs, section).selected = true;

    var $tabPanel = Ox.TabPanel({
            content: function(id) {
                if (id == 'general') {
                    return pandora.ui.listGeneralPanel(listData);
                } else if (id == 'icon') {
                    return pandora.ui.listIconPanel(listData);
                } else if (id == 'query') {
                    return pandora.$ui.filter = pandora.ui.filter(listData);
                }
            },
            tabs: tabs
        })
        .bindEvent({
            change: function(data) {
                var width = getWidth(data.selected);
                $dialog.options({
                    maxWidth: width,
                    minWidth: width,
                    title: 'Smart List - ' + listData.name + ' - '
                        + Ox.getObjectById(tabs, data.selected).title
                });
                $dialog.setSize(width, 312);
                $findElement[data.selected == 'icon' ? 'show' : 'hide']();
            }
        });

    var $findElement = Ox.FormElementGroup({
            elements: [
                pandora.$ui.findIconItemSelect = Ox.Select({
                    items: pandora.site.findKeys,
                    overlap: 'right',
                    type: 'image'
                })
                .bindEvent({
                    change: function(data) {

                    }
                }),
                pandora.$ui.findIconItemInput = Ox.Input({
                    changeOnKeypress: true,
                    clear: true,
                    placeholder: 'Find: Foo',
                    width: 120 + Ox.UI.SCROLLBAR_SIZE
                })
                .bindEvent({
                    change: function(data) {

                    }
                })
            ],
        })
        .css({
            float: 'right',
            margin: '4px',
            align: 'right'
        });
    if (section != 'icon') {
        $findElement.hide();
    }
    $findElement.appendTo($tabPanel.children('.OxBar'));


    var $dialog = Ox.Dialog({
        buttons: [
            Ox.Button({
                    id: 'debug',
                    title: 'Debug',
                })
                .bindEvent({
                    click: function() {
                        alert(JSON.stringify(pandora.$ui.filter.options('query')));
                    }
                }),
            Ox.Button({
                    id: 'done',
                    title: 'Done'
                })
                .bindEvent({
                    click: function() {
                        $dialog.close();
                    }
                })
        ],
        content: $tabPanel,
        maxWidth: width,
        minHeight: 312,
        minWidth: width,
        height: 312,
        // keys: {enter: 'save', escape: 'cancel'},
        title: 'Smart List - ' + listData.name,
        width: width
    });

    function getWidth(section) {
        return section == 'general' ? 496
            : (section == 'icon' ? 696 : 648) + Ox.UI.SCROLLBAR_SIZE;
    }

    return $dialog;

};

pandora.ui.listGeneralPanel = function(listData) {
    var that = Ox.Element({}),
        $icon = $('<img>')
            .attr({src: '/list/' + listData.id + '/icon256.jpg?' + Ox.uid()})
            .css({position: 'absolute', left: '16px', top: '16px', width: '128px', height: '128px', borderRadius: '32px'})
            .appendTo(that),
        $nameInput = Ox.Input({
                label: 'Name',
                labelWidth: 80,
                value: listData.name,
                width: 320
            })
            .css({position: 'absolute', left: '160px', top: '16px'})
            .appendTo(that),
        $itemsInput = Ox.Input({
                disabled: true,
                label: 'Items',
                labelWidth: 80,
                value: listData.items,
                width: 320
            })
            .css({position: 'absolute', left: '160px', top: '40px'})
            .appendTo(that),
        $statusSelect = Ox.Select({
                items: [
                    {id: 'private', title: 'Private', selected: listData.status == 'private'},
                    {id: 'public', title: 'Public', selected: listData.status == 'public'},
                    {id: 'featured', title: 'Featured', selected: listData.status == 'featured'},
                ],
                label: 'Status',
                labelWidth: 80,
                width: 320
            })
            .css({position: 'absolute', left: '160px', top: '64px'})
            .appendTo(that),
        $subscribersInput = Ox.Input({
                disabled: true,
                label: 'Subscribers',
                labelWidth: 80,
                value: 0,
                width: 320
            })
            .css({position: 'absolute', left: '160px', top: '88px'})
            .appendTo(that);
    return that;
};

pandora.ui.listIconPanel = function(listData) {

    var quarter = 0,
        quarters = ['top-left', 'top-right', 'bottom-left', 'bottom-right'],

        $iconPanel = Ox.Element(),

        $icon = $('<img>')
            .attr({src: '/list/' + listData.id + '/icon256.jpg?' + Ox.uid()})
            .css({position: 'absolute', borderRadius: '64px', margin: '16px'})
            .appendTo($iconPanel),

        $previewPanel = Ox.Element(),

        $preview,

        $list = Ox.Element(),

        that = Ox.SplitPanel({
            elements: [
                {
                    element: $iconPanel,
                    size: 280
                },
                {
                    element: $previewPanel
                },
                {
                    element: $list,
                    size: 144 + Ox.UI.SCROLLBAR_SIZE
                }
            ],
            orientation: 'horizontal'
        });

    pandora.api.findLists({
        query: {
            conditions: [{key: 'id', value: listData.id, operator: '=='}],
            operator: '&'
        },
        keys: ['posterFrames']
    }, function(result) {

        var posterFrames = result.data.items[0].posterFrames,
            posterFrame = posterFrames[quarter],

            $interface = Ox.Element({
                    tooltip: function(e) {
                        return 'Edit ' + $(e.target).attr('id').replace('-', ' ') + ' image';
                    }
                })
                .css({
                    position: 'absolute',
                    width: '256px',
                    height: '256px',
                    marginLeft: '16px',
                    marginTop: '16px',
                    cursor: 'pointer'
                })
                .bind({
                    click: function(e) {
                        clickIcon(e);
                    },
                    dblclick: function(e) {
                        clickIcon(e, true);
                    }
                })
                .appendTo($iconPanel);

        renderQuarters();

        $list = Ox.IconList({
            borderRadius: 16,
            item: function(data, sort) {
                var size = 128;
                return {
                    height: size,
                    id: data.id,
                    info: data[['title', 'director'].indexOf(sort[0].key) > -1 ? 'year' : sort[0].key],
                    title: data.title + (data.director.length ? ' (' + data.director.join(', ') + ')' : ''),
                    url: '/' + data.id + '/icon' + size + '.jpg',
                    width: size
                };
            },
            items: function(data, callback) {
                //Ox.Log('', 'data, pandora.Query.toObject', data, pandora.Query.toObject())
                pandora.api.find(Ox.extend(data, {
                    query: {
                        conditions: [{key: 'list', value: listData.id, operator: '='}],
                        operator: '&'
                    }
                }), callback);
            },
            keys: ['director', 'duration', 'id', 'posterFrame', 'title', 'videoRatio', 'year'],
            max: 1,
            min: 1,
            //orientation: 'vertical',
            selected: posterFrame ? [posterFrame.item] : [],
            size: 128,
            sort: pandora.user.ui.listSort,
            unique: 'id'
        })
        //.css({width: '144px'})
        .bindEvent({
            open: function(data) {
                setPosterFrame(data.ids[0], $list.value(data.ids[0], 'posterFrame'))
            },
            select: function(data) {
                renderPreview($list.value(data.ids[0]));
            }
        })
        .bindEventOnce({
            load: function() {
                var itemData;
                if (!posterFrame) {
                    itemData = $list.value(0);
                    $list.options({selected: [itemData.id]});
                } else {
                    itemData = $list.value(posterFrame.item);
                }
                renderPreview(itemData);
            }
        })
        .gainFocus();

        that.replaceElement(2, $list);

        function clickIcon(e, isDoubleClick) {
            quarter = quarters.indexOf($(e.target).attr('id'));
            renderQuarters();
            if (isDoubleClick) {
                var item = posterFrames[quarter].item;
                $list.options({selected: [item]});
                renderPreview($list.value(item), posterFrames[quarter].position);
            }
        }

        function renderPreview(itemData, position) {
            $preview = pandora.ui.videoPreview({
                duration: itemData.duration,
                frameRatio: itemData.videoRatio,
                height: 256,
                id: itemData.id,
                position: position,
                width: 256
            })
            .css({marginLeft: '8px', marginTop: '16px', overflow: 'hidden'})
            .bindEvent({
                click: function(data) {
                    setPosterFrame(itemData.id, data.position);
                }
            });
            /*
            // fixme: need canvas for this
            $($preview.children('.OxFrame')[0])
                .css('border-' + quarter + '-radius', '128px');
            */
            $previewPanel.empty().append($preview);
        }

        function renderQuarters() {
            $interface.empty();
            quarters.forEach(function(q, i) {
                $interface.append(
                    $('<div>')
                        .attr({id: q})
                        .css({
                            float: 'left',
                            width: '126px',
                            height: '126px',
                            border: '1px solid rgba(255, 255, 255, ' + (i == quarter ? 0.75 : 0) + ')',
                            background: 'rgba(0, 0, 0, ' + (i == quarter ? 0 : 0.75) + ')'
                        })
                        .css('border-' + q + '-radius', '64px')
                );
            });
        }

        function setPosterFrame(item, position) {
            var posterFrame = {item: item, position: position};
            if (posterFrames.length) {
                posterFrames[quarter] = posterFrame;
            } else {
                posterFrames = Ox.repeat([posterFrame], 4);
            }
            pandora.api.editList({
                id: listData.id,
                posterFrames: posterFrames
            }, function() {
                $icon.attr({src: '/list/' + listData.id + '/icon256.jpg?' + Ox.uid()});
            });
            $preview.options({position: position});
        }

    });

    function renderFrame() {
        $frame.css({borderRadius: 0});
        $frame.css('border-' + quarters[quarter] + '-radius', '128px');
    }


    return that;

}
