// vim: et:ts=4:sw=4:sts=4:ft=javascript

'use strict';

// fixme: this should be deleted!!

pandora.ui.annotations = function() {
    var that = Ox.Element({
            id: 'annotations'
        })
        .bindEvent({
            resize: function(data) {
                pandora.user.ui.annotationsSize = data.size;
            },
            resizeend: function(data) {
                pandora.UI.set({annotationsSize: data.size});
            },
            toggle: function(data) {
                pandora.UI.set({showAnnotations: !data.collapsed});
            }
        }),
        $bins = [];
    pandora.site.layers.forEach(function(layer) {
        var $bin = Ox.CollapsePanel({
            id: layer.id,
            size: 16,
            title: layer.title
        });
        $bins.push($bin);
        $bin.$content.append(
            $('<div>').css({ height: '20px' }).append(
                $('<div>').css({ float: 'left', width: '16px', height: '16px', margin: '1px'}).append(
                    $('<img>').attr({ src: Ox.UI.getImageURL('iconFind') }).css({ width: '16px', height: '16px', border: 0, background: 'rgb(64, 64, 64)', WebkitBorderRadius: '2px' })
                )
            ).append(
                $('<div>').css({ float: 'left', width: '122px', height: '14px', margin: '2px' }).html('Foo')
            ).append(
                $('<div>').css({ float: 'left', width: '40px', height: '14px', margin: '2px', textAlign: 'right' }).html('23')
            )
        );
    });
    $bins.forEach(function(bin) {
        that.append(bin);
    });
    return that;
};



