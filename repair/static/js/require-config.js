requirejs.config({
  baseUrl: '/static/js',
  paths: {
    'almond': 'libs/almond',
    'flowmap': 'app/visualizations/flowmap',
    'mapviewer': 'app/visualizations/mapviewer',
    'd3': 'libs/d3.v3.min',
    'leaflet': 'libs/leaflet',
    'esri-leaflet': 'libs/esri-leaflet',
    'leaflet-fullscreen': 'libs/leaflet.fullscreen.min',
    'openlayers': 'libs/ol',
    'ol-contextmenu': 'libs/ol-contextmenu',
    'spatialsankey': 'libs/spatialsankey',
    'cyclesankey': 'libs/cycle-sankey',
    'jquery': 'libs/jquery-3.2.1.min',
    'bootstrap': 'libs/bootstrap',
    'treeview': 'libs/bootstrap-treeview.min',
    'backbone': 'libs/backbone-min',
    'underscore': 'libs/underscore-min',
    'cookies': 'libs/js.cookie',
    'tablesorter': 'libs/jquery.tablesorter.widgets',
    'tablesorter-pager': 'libs/jquery.tablesorter.pager'
  },
  shim: {
    'almond': { exports: 'almond' },
    'tablesorter': { deps: ['libs/jquery.tablesorter.min'] },
    'tablesorter-pager': { deps: ['tablesorter'] },
    'leaflet-fullscreen': { deps: ['leaflet'] },
    'backbone': { deps: ['jquery', 'underscore']},
    'spatialsankey': { deps: ['d3'] },
    'cyclesankey': { deps: ['d3'] },
    'bootstrap': { deps: ['jquery'], exports: '$.fn.popover' }
  }
});

/* OVERRIDE FUNCTIONS */

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

// force Backbone to add a trailing Slash to urls (Django is picky with that)
require(['backbone'], function (Backbone) {
  var _sync = Backbone.sync;
  Backbone.sync = function(method, model, options){
    // Add trailing slash to backbone model views
    var parts = _.result(model, 'url').split('?'),
      _url = parts[0],
      params = parts[1];

    _url += _url.charAt(_url.length - 1) == '/' ? '' : '/';

    if (!_.isUndefined(params)) {
      _url += '?' + params;
    };

    options = _.extend(options, {
      url: _url
    });

    return _sync(method, model, options);
  };
});

// add the csrf-token to all unsafe requests, otherwise django would deny access
require(['jquery', 'cookies'], function ($, Cookies) {
  var csrftoken = Cookies.get('csrftoken');
  function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
  }
  $.ajaxSetup({
    beforeSend: function(xhr, settings) {
      if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
        xhr.setRequestHeader("X-CSRFToken", csrftoken);
      }
    }
  });
});
