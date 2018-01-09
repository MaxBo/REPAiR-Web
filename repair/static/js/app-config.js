define(['browser-cookies'],
  function (cookies) {
  
    var config = {
      URL: '/' // base application URL
    };
    
    config.getSession = function(callback){
    
      //var sessionid = cookies.get('sessionid');
      //console.log(sessionid)
      fetch('/login/session', {
          headers: {
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
          },
          credentials: 'include'
        }).then(response => response.json()).then(json => callback(json));
    }
    
    config.api = {
      base:                 '/api', // base Rest-API URL
      stakeholders:         '/api/stakeholders/',
      casestudies:          '/api/casestudies/',
      materials:            '/api/materials/',
      keyflows:             '/api/keyflows/',
      qualities:            '/api/qualities',
      keyflowsInCaseStudy:  '/api/casestudies/{0}/keyflows',
      activitygroups:       '/api/casestudies/{0}/keyflows/{1}/activitygroups',
      activities:           '/api/casestudies/{0}/keyflows/{1}/activities',
      actors:               '/api/casestudies/{0}/keyflows/{1}/actors',
      adminLocations:       '/api/casestudies/{0}/keyflows/{1}/administrativelocations',
      opLocations:          '/api/casestudies/{0}/keyflows/{1}/operationallocations',
      activitiesInGroup:    '/api/casestudies/{0}/keyflows/{1}/activitygroups/{2}/activities',
      actorsInActivity:     '/api/casestudies/{0}/keyflows/{1}/activitygroups/{2}/activities/{3}/actors',
      products:             '/api/casestudies/{0}/keyflows/{1}/products',
      activityToActivity:   '/api/casestudies/{0}/keyflows/{1}/activity2activity/',
      groupToGroup:         '/api/casestudies/{0}/keyflows/{1}/group2group/',
      actorToActor:         '/api/casestudies/{0}/keyflows/{1}/actor2actor/',
      groupStock:           '/api/casestudies/{0}/keyflows/{1}/groupstock/',
      activityStock:        '/api/casestudies/{0}/keyflows/{1}/activitystock/',
      actorStock:           '/api/casestudies/{0}/keyflows/{1}/actorstock/'
    };
  
    return config;
  }
);

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
require(['backbone', 'underscore'], function (Backbone, _) {
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
require(['jquery', 'browser-cookies'], function ($, cookies) {
  console.log(document.cookie)
  var csrftoken = cookies.get('csrftoken');
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
