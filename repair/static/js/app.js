requirejs.config({
    baseUrl: '/static/js',
    paths: {
        almond: 'libs/almond',
        map: 'app/visualizations/map',
        flowmap: 'app/visualizations/flowmap',
        mapviewer: 'app/visualizations/mapviewer',
        d3: 'libs/d3.v3.min',
        leaflet: 'libs/leaflet',
        spatialsankey: 'libs/spatialsankey'
    },
    shim: {
        almond: { exports: 'almond' }
    }
});
