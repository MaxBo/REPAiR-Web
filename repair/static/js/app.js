requirejs.config({
    baseUrl: '/static/js',
    paths: {
        almond: 'libs/almond',
        map: 'visualizations/map',
        d3: 'libs/d3.v3.min',
        leaflet: 'libs/leaflet',
        spatialsankey: 'libs/spatialsankey'
    },
    shim: {
        almond: {exports: 'almond'}
    }
});

requirejs(['app/main']);