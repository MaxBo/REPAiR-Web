define([
  'd3',
  'models/casestudy',
  'visualizations/sankey-map',
  'views/study-area/base-maps',
  'views/study-area/base-charts',
  'app-config',
  'base'
], function(d3, CaseStudy, MapView, BaseMapsView, BaseChartsView, appConfig) {

  function renderWorkshop(){
    NodeHandler = function(){
      this.id = 0;
      var callbacks = [];
      
      this.add = function(callback){
        callbacks.push(callback);
      }
      
      this.changeActive = function(id){
        this.id = id;
        callbacks.forEach(function(callback){
          callback(id);
        });
      }
    }
  
    var handler = new NodeHandler();
    
    var callbackTest = function(id){
      document.getElementById('nodeinfo').innerHTML = "Node ID: " + id;
    }
    
    handler.add(callbackTest);
    
    var map = new MapView({
      divid: 'map', 
      nodes: '/static/data/nodes.geojson', 
      links: '/static/data/links.csv',
      nodeHandler: handler
    });
  }
  
  var session = appConfig.getSession(
    function(session){
      var mode = session['mode'];
      if (Number(mode) == 1) {
        var caseStudyId = session['casestudy'];
        caseStudy = new CaseStudy({id: caseStudyId});
      
        caseStudy.fetch({success: function(){
          renderSetup(caseStudy)
        }});
      }
      else
        renderWorkshop()
  });
  
  function renderSetup(caseStudy){
    var mapsView = new BaseMapsView({
      template: 'base-map-template',
      el: document.getElementById('base-map-setup'),
      caseStudy: caseStudy
    });
    
    var chartsView = new BaseChartsView({
      template: 'base-charts-template',
      el: document.getElementById('base-charts-setup'),
      caseStudy: caseStudy
    })
  }
  
});