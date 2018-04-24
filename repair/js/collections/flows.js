define(["backbone", "app-config"],

  function(Backbone, config) {
  
   /**
    *
    * @author Christoph Franke
    * @name module:collections/Flows
    * @augments Backbone.Collection
    */
    var Flows = Backbone.Collection.extend(
      /** @lends module:collections/Flows.prototype */
      {
      /**
       * generates an url to the api resource based on the ids and type given in constructor
       *
       * @returns {string} the url string
       */
      url: function(){
        var url = (this.type == 'activity') ? config.api.activityToActivity:
                  (this.type == 'actor') ? config.api.actorToActor:
                  config.api.groupToGroup;
        return url.format(this.caseStudyId, this.keyflowId);
      },
      
      /**
       * @returns {number} number of connections to node with given id
       */
      nConnections: function(id){
        filtered = this.filter(function (model) {
            return (model.get("origin") === id) || (model.get("destination") === id);
        });
        return filtered.length
      },
      
    /**
     * collection for fetching/putting flows
     *
     * @param {Object} [attributes=null]         fields of the model and their values, will be set if passed
     * @param {Object} options
     * @param {string} options.caseStudyId       id of the casestudy the flows belong to
     * @param {string} options.keyflowId         id of the keyflow the flows belong to
     * @param {string} [options.type='group']    type of nodes connected by the flows ('activity', 'actor' or 'group')
     *
     * @constructs
     * @see http://backbonejs.org/#Collection
     */
      initialize: function (attrs, options) {
        this.caseStudyId = options.caseStudyId;
        this.keyflowId = options.keyflowId;
        this.type = options.type;
      }
    });
    
    return Flows;
  }
);