requirejs.config({
    baseUrl: '/static/js',
    paths: {
        almond: 'libs/almond',
        map: 'visualizations/map',
        flowmap: 'visualizations/flowmap',
        mapviewer: 'visualizations/mapviewer',
        d3: 'libs/d3.v3.min',
        leaflet: 'libs/leaflet',
        spatialsankey: 'libs/spatialsankey'
    },
    shim: {
        almond: {exports: 'almond'}
    }
});

function ready(fn) {
  if (document.readyState != 'loading'){
    fn();
  } else if (document.addEventListener) {
    document.addEventListener('DOMContentLoaded', fn);
  } else {
    document.attachEvent('onreadystatechange', function() {
      if (document.readyState != 'loading')
        fn();
    });
  }
}

ready(function() {requirejs(['app/study-sankey'])});