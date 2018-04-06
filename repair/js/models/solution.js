define(["backbone", "app-config", 'utils/utils'],

  function(Backbone, config, utils) {

   /**
    *
    * @author Christoph Franke
    * @name module:models/Solution
    * @augments Backbone.Model
    */
    var Solution = Backbone.Model.extend(
      /** @lends module:models/Solution.prototype */
      {
      idAttribute: "id",
      
      fileAttributes: ['activities_image', 'currentstate_image', 'effect_image'],
      
      defaults: {
        name: '-----',
        description: '',
        one_unit_equals: '',
        service_layers: '',
        activities: [],
        activities_image: null,
        currentstate_image: null,
        effect_image: null
      },
      
      /**
       * generates an url to the api resource based on the ids given in constructor
       *
       * @returns {string} the url string
       */
      urlRoot: function(){
        if ((this.caseStudyId == null || this.solutionCategoryId == null) && this.collection )
          return this.collection.url()
        return config.api.solutions.format(this.caseStudyId, this.solutionCategoryId);
      },
      
      save: function(data, options){
        var _this = this,
            uploadAsForm = false,
            data = data || {};
        this.fileAttributes.forEach(function(attr){
          if (attr in data) uploadAsForm = true;
        });
        
        // if file is passed in data: upload as form
        if (uploadAsForm){
          // remove trailing slash if there is one
          var url = this.urlRoot().replace(/\/$/, "");
          // post to resource if already existing (indicated by id) else create by posting to list view
          if (this.id != null) url += '/' + this.id;
          url += '/';
          utils.uploadForm(data, url, {
              method: (this.id != null) ? 'PUT': 'POST',
              success: function(resData, textStatus, jqXHR){
                  // set attributes corresponding to response
                  for(key in resData){
                      _this.attributes[key] = resData[key];
                  }
                  if (options.success) options.success(_this);
              },
              error: options.error
          })
        }
        else Solution.__super__.save.apply(this, [data, options]);
      },

    /**
     * model for fetching/putting defintions of a solution
     *
     * @param {Object} [attributes=null]          fields of the model and their values, will be set if passed
     * @param {Object} options
     * @param {string} options.caseStudyId        id of the casestudy the solution belong to
     * @param {string} options.solutionCategoryId id of the category the solution belong to
     *
     * @constructs
     * @see http://backbonejs.org/#Model
     */
      initialize: function (attributes, options) {
        this.caseStudyId = options.caseStudyId;
        this.solutionCategoryId = options.solutionCategoryId;
      },

    });
    return Solution;
  }
);