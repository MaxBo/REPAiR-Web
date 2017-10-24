requirejs.config({
  baseUrl: '/static/js',
  paths: {
    'almond': 'libs/almond',
    'map': 'app/visualizations/map',
    'flowmap': 'app/visualizations/flowmap',
    'mapviewer': 'app/visualizations/mapviewer',
    'd3': 'libs/d3.v3.min',
    'leaflet': 'libs/leaflet',
    'esri-leaflet': 'libs/esri-leaflet',
    'leaflet-fullscreen': 'libs/leaflet.fullscreen.min',
    'spatialsankey': 'libs/spatialsankey',
    'cyclesankey': 'libs/cycle-sankey',
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
    'spatialsankey': { deps: ['d3'] },
    'cyclesankey': { deps: ['d3'] },
  }
});

/* String formatter taken from https://stackoverflow.com/questions/610406/javascript-equivalent-to-printf-string-format
example: "{0} is dead, but {1} is alive! {0} {2}".format("ASP", "ASP.NET")
*/
if (!String.prototype.format) {
  String.prototype.format = function() {
    var args = arguments;
    return this.replace(/{(\d+)}/g, function(match, number) { 
      return typeof args[number] != 'undefined'
        ? args[number]
        : match
      ;
    });
  };
}
