define([],
  function () {
  
    var config = {
      URL: '/' // base application URL
    };
    
    config.api = {
      base:              '/api', // base Rest-API URL
      stakeholders:      '/api/stakeholders/',
      casestudies:       '/api/casestudies/',
      activitygroups:    '/api/casestudies/{0}/activitygroups',
      activities:        '/api/casestudies/{0}/activities',
      actors:            '/api/casestudies/{0}/actors',
      activitiesInGroup: '/api/casestudies/{0}/activitygroups/{1}/activities',
      actorsInActivity:  '/api/casestudies/{0}/activitygroups/{1}/activities/{2}/actors'
    };
  
    return config;
  }
);
