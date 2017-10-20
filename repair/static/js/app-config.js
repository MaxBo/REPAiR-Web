define([],
  function () {
  
    var config = {
      URL: '/' // base application URL
    };
    
    config.api = {
      base:           '/api', // base Rest-API URL
      casestudies:    '/api/casestudy/',
      activitygroups: '/api/casestudy/{0}/activitygroups',
      stakeholders:   '/api/stakeholders/'
    };
  
    return config;
  }
);
