require(['./libs/domReady!', './app'], function (doc, app) {
    requirejs(['app/evaluation-map']);
    requirejs(['app/flow-map']);
});