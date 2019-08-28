
define(['views/common/baseview', 'underscore', 'collections/gdsecollection',
        'models/gdsemodel', 'visualizations/map', 'app-config', 'utils/utils', 'bootstrap',
        'bootstrap-select'],

function(BaseView, _, GDSECollection, GDSEModel, Map, config, utils){
/**
*
* @author Christoph Franke
* @name module:views/PossibleImplementationAreaView
* @augments BaseView
*/
var PossibleImplementationAreaView = BaseView.extend(
    /** @lends module:views/PossibleImplementationAreaView.prototype */
    {

    /**
    *
    *
    * @param {Object} options
    * @param {HTMLElement} options.el                          element the view will be rendered in
    * @param {string} options.template                         id of the script element containing the underscore template to render this view
    * @param {module:models/CaseStudy} options.caseStudy       the casestudy to add solutions to
    *
    * @constructs
    * @see http://backbonejs.org/#View
    */
    initialize: function(options){
        PossibleImplementationAreaView.__super__.initialize.apply(this, [options]);
        var _this = this;

        this.template = 'area-template';
        this.solutions = options.solutions;
        this.caseStudy = options.caseStudy;

        this.render();
    },

    /*
    * dom events (managed by jquery)
    */
    events: {
        'click button[name="show-area"]': 'showArea',
        'click button[name="set-focus-area"]': 'setFocusArea',
        'click button[name="set-casestudy"]': 'setCaseStudy'
    },

    /*
    * render the view
    */
    render: function(){
        var _this = this,
            html = document.getElementById(this.template).innerHTML,
            template = _.template(html);
        this.el.innerHTML = template({});

        this.implAreaText = this.el.querySelector('textarea[name="implementation-area"]');
        this.questionInput = this.el.querySelector('input[name="question"]');
        var mapDiv = this.el.querySelector('div[name="area-map"]');
        this.areaMap = new Map({
            el: mapDiv
        });
        this.areaMap.addLayer('implementation-area', {
            stroke: 'rgb(0, 98, 255)',
            fill: 'rgba(0, 98, 255, 0.1)',
            strokeWidth: 1,
            zIndex: 0
        });
        this.setInputs();
    },

    setInputs: function(){
        var implArea = this.model.get('geom') || '';
        if(implArea) implArea = JSON.stringify(implArea);
        this.implAreaText.value = implArea;
        this.questionInput.value = this.model.get('question') || '';
        this.showArea();
    },

    applyInputs: function(){
        var geoJSON = this.checkGeoJSON(this.implAreaText.value);
        this.model.set('geom', geoJSON);
        this.model.set('question', this.questionInput.value);
    },

    showArea: function(){
        var implArea = this.implAreaText.value;
        if (!implArea) return;

        var geoJSON = this.checkGeoJSON(implArea);
        if (!geoJSON) return;

        this.areaMap.clearLayer('implementation-area');
        try {
            var poly = this.areaMap.addPolygon(geoJSON.coordinates, {
                projection: this.projection,
                layername: 'implementation-area',
                tooltip: gettext('possible implementation area'),
                type: geoJSON.type.toLowerCase()
            });
        }
        catch(err) {
            this.alert(err);
            return;
        }
        this.areaMap.centerOnPolygon(poly, { projection: this.projection });
    },

    checkGeoJSON: function(geoJSONTxt){
        try {
            var geoJSON = JSON.parse(geoJSONTxt);
        }
        catch(err) {
            this.alert(err);
            return;
        }
        if (!geoJSON.coordinates && !geoJSON.type) {
            this.alert(gettext('GeoJSON needs attributes "type" and "coordinates"'));
        }
        if (!['multipolygon', 'polygon'].includes(geoJSON.type.toLowerCase())){
            this.alert(gettext('type has to be MultiPolygon or Polygon'));
            return;
        }
        return geoJSON;
    },

    setFocusArea: function(){
        var focusArea = this.caseStudy.get('properties').focusarea;
        if (!focusArea) {
            this.onError(gettext('focus area is not set for this case study'));
            return;
        }
        this.implAreaText.value = JSON.stringify(focusArea);
        this.showArea();
    },

    setCaseStudy: function(){
        var geom = this.caseStudy.get('geometry');
        if (!geom) {
            this.alert(gettext('case study region is not set for this case study'));
            return;
        }
        this.implAreaText.value = JSON.stringify(geom);
        this.showArea();
    },

});
return PossibleImplementationAreaView;
}
);
