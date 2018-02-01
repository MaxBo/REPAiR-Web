
define(['models/casestudy', 'views/data-entry-flows',
        'views/data-entry-actors', 'views/data-entry-materials', 
        'collections/flows', 'collections/actors',
        'collections/keyflows', 'collections/materials',
        'app-config', 'utils/loader', 'base'], // workaround: overrides.js is already loaded in base.js, but there seem to be two conflicting jquery instances
function (CaseStudy, FlowsView, ActorsView, EditMaterialsView, Flows, 
          Actors, Keyflows, Materials,
          appConfig, Loader) {  
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
      activities,
      materials;

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
      materials = new Materials([], { caseStudyId: caseStudy.id, keyflowId: keyflow.id });
      var loader = new Loader(document.getElementById('content'),
                              { disable: true });
      materials.fetch({success: function(){
        loader.remove();
        renderFlows(keyflow);
        renderEditActors(keyflow);
        renderEditMaterials(keyflow);
      }});
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
        document.getElementById('casestudy-warning').style.display = 'block';
        document.getElementById('keyflow-warning').style.display = 'none';
        return;
      }
      caseStudy = new CaseStudy({id: caseStudyId});
      keyflows = new Keyflows([], {caseStudyId: caseStudyId});
      var loader = new Loader(document.getElementById('content'),
                              {disable: true});
      $.when(caseStudy.fetch(),  keyflows.fetch()).then(function() {
        loader.remove();
        render(caseStudy);
      });
  });
});