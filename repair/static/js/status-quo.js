require(['./libs/domReady!', './require-config'], function (doc, config) {
    requirejs(['app/evaluation-map']);
    requirejs(['app/flow-map']);
});