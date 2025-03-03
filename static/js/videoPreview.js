'use strict';

pandora.ui.videoPreview = function(data) {
    var that = Ox.VideoPreview({
            duration: data.duration,
            getFrame: function(position) {
                var resolutions = pandora.site.video.resolutions.filter(function(resolution, i) {
                        return resolution >= data.height;
                    }),
                    resolution = resolutions.length
                        ? Ox.min(resolutions)
                        : Ox.max(pandora.site.video.resolutions);
                return pandora.getMediaURL('/' + data.id + '/' + resolution + 'p' + (
                    Ox.isUndefined(position) ? '' : position
                ) + '.jpg?' + data.modified);
            },
            frameRatio: data.frameRatio,
            height: data.height,
            position: data.position,
            scaleToFill: true,
            timeline: pandora.getMediaURL('/' + data.id + '/timeline16p.jpg?' + data.modified),
            videoTooltip: data.videoTooltip,
            width: data.width
        });
    return that;
};

