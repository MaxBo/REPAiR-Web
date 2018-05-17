
define(['models/casestudy', 'views/data-entry/flows',
        'views/data-entry/actors', 'views/data-entry/materials', 
        'collections/gdsecollection', 
        'app-config', 'utils/utils', 'base'], 
function (CaseStudy, FlowsView, ActorsView, EditMaterialsView, GDSECollection, 
          appConfig, utils) {  
  /**
   *
   * entry point for data-entry, 
   * render tabs for entering data (edit actors, flows and materials)
   *
   * @author Christoph Franke
   * @module DataEntry
   */
  var _ = require('underscore');
  var caseStudy,
      keyflows,
      materials,
      activities,
      loader = new utils.Loader(document.getElementById('content'), {disable: true});

  var flowsView,
      actorsView,
      editMaterialsView;
      
  var refreshFlowsBtn = document.getElementById('refresh-flowview-btn'),
      refreshMaterialsBtn = document.getElementById('refresh-materialsview-btn'),
      refreshActorsBtn = document.getElementById('refresh-actorsview-btn');

  function renderFlows(keyflow){
    if (keyflow == null) return;
    if (flowsView != null)
      flowsView.close();
    flowsView = new FlowsView({
      el: document.getElementById('flows-content'),
      template: 'flows-edit-template',
      model: keyflow,
      materials: materials, 
      activities: activities,
      caseStudy: caseStudy
    });
    refreshFlowsBtn.style.display = 'block';
  };
  
  function renderEditActors(keyflow){
    if (keyflow == null) return;
    if (actorsView != null)
      actorsView.close();
    // create casestudy-object and render view on it (data will be fetched in view)

    actorsView = new ActorsView({
      el: document.getElementById('actors-content'),
      template: 'actors-template',
      model: keyflow,
      caseStudy: caseStudy,
      activities: activities,
      onUpload: function(){renderEditActors(keyflow)}
    });
    refreshActorsBtn.style.display = 'block';
  };
  
  function renderEditMaterials(keyflow){
    if (keyflow == null) return;
    if (editMaterialsView != null)
      editMaterialsView.close();

    // create casestudy-object and render view on it (data will be fetched in view)

    editMaterialsView = new EditMaterialsView({
      el: document.getElementById('materials-content'),
      template: 'materials-edit-template',
      model: keyflow,
      caseStudy: caseStudy,
      materials: materials
    });
    refreshMaterialsBtn.style.display = 'block';
  };

  function render(caseStudy){

    var keyflowSelect = document.getElementById('keyflow-select');
    function getKeyflow(){
      return keyflows.get(keyflowSelect.value);
    }
    document.getElementById('keyflow-warning').style.display = 'block';
    keyflowSelect.addEventListener('change', function(){
      var keyflow = getKeyflow();
      document.getElementById('keyflow-warning').style.display = 'none';
      materials = new GDSECollection([], { 
        apiTag: 'materials', 
        apiIds: [ caseStudy.id, keyflow.id ] 
      });
      activities = new GDSECollection([], { 
          apiTag: 'activities',
          apiIds: [ caseStudy.id, keyflow.id ]
      });
      loader.activate();
      Promise.all([materials.fetch(), activities.fetch()]).then(function(){
        loader.deactivate();
        renderFlows(keyflow);
        renderEditActors(keyflow);
        renderEditMaterials(keyflow);
      });
    });
    refreshFlowsBtn.addEventListener('click', function(){ renderFlows(getKeyflow()) });
    refreshMaterialsBtn.addEventListener('click', function(){ renderEditMaterials(getKeyflow()) });
    refreshActorsBtn.addEventListener('click', function(){ renderEditActors(getKeyflow()) });
    document.getElementById('keyflow-select').disabled = false;
  }

  var session = appConfig.getSession(
    function(session){
      var caseStudyId = session['casestudy'];
      if (caseStudyId == null){
        document.getElementById('keyflow-warning').style.display = 'none';
        return;
      }
      caseStudy = new CaseStudy({ id: caseStudyId });
      keyflows = new GDSECollection([], { 
        apiTag: 'keyflowsInCaseStudy', 
        apiIds: [caseStudyId] 
      });
      loader.activate();
      $.when(caseStudy.fetch(),  keyflows.fetch()).then(function() {
        loader.deactivate();
        render(caseStudy);
      });
  });
});