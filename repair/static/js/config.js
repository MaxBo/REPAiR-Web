requirejs.config({
    baseUrl: '/static/js',
    paths: {
        'almond': 'libs/almond',
        'map': 'app/visualizations/map',
        'flowmap': 'app/visualizations/flowmap',
        'mapviewer': 'app/visualizations/mapviewer',
        'd3': 'libs/d3.v3.min',
        'leaflet': 'libs/leaflet',
        'spatialsankey': 'libs/spatialsankey',
        'jquery': 'libs/jquery-3.2.1.min',
        'treeview': 'libs/bootstrap-treeview.min',
        'backbone': 'libs/backbone-min',
        'underscore': 'libs/underscore-min'
    },
    shim: {
        'almond': { exports: 'almond' },
        'backbone': {
            deps: ['underscore', 'jquery']
        },
    }
});
