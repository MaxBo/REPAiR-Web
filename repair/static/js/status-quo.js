require(['./libs/domReady!', './config'], function (doc, config) {
    requirejs(['app/evaluation-map']);
    requirejs(['app/flow-map']);
});