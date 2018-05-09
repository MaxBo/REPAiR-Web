define(["backbone-pageable", "backbone", "underscore", "app-config"],

function(PageableCollection, Backbone, _, config) {

    // default model, you might add some extra common stuff here
    var GDSEModel = Backbone.Model.extend( {
        idAttribute: "id"
    });

    /**
    *
    * @author Christoph Franke
    * @name module:collections/GDSECollection
    * @augments Backbone.PageableCollection
    *
    * @see https://github.com/backbone-paginator/backbone.paginator
    */
    var GDSECollection = PageableCollection.extend(
        /** @lends module:collections/GDSECollection.prototype */
        {
        /**
        * generates an url to the api resource list based on the ids given in constructor
        *
        * @returns {string} the url string
        */
        url: function(){
            // if concrete url was passed: take this and ignore the rest
            if (this.baseurl) return this.baseurl;
            
            var apiUrl = config.api[this.apiTag]
            if (this.apiIds != null && this.apiIds.length > 0)
                apiUrl = apiUrl.format(...this.apiIds);
            return apiUrl
        },
        
        // by default try to fetch 'em all
        state: {
            pageSize: 1000000,
            firstPage: 1,
            currentPage: 1
        },

        /**
        * filter the collection by its attributes
        * the values to each attribute have to be an exact match to add a model to the returned results
        *
        * @param {Object} options            key/value pairs of attribute names and the values to match
        *
        * @returns {Array.<Backbone.model>}  list of all models matching the passed attribute/value combinations
        */
        filterBy: function (options) {
            var options = options || {};
            var filtered = this.filter(function (model) {
                var match = true;
                for (var key in options) {
                    match &= (String(model.get(key)) == String(options[key]));
                }
                return match;
            });
            return filtered;
        },

        queryParams: {
            pageSize: "page_size"
        },

        parseRecords: function (response) {
            // paginated api urls return the models under the key 'results'
            if (response.results)
                return response.results;
            return response;
        },

        /**
        * collection
        *
        * @param {Array.<Backbone.model>} models   list objects representing the fields of each model and their values, will be set if passed
        * @param {Object} options
        * @param {string} options.baseurl          static url (overrides all api arguments)
        * @param {string} options.apiTag           key of url as in config.api
        * @param {string} options.apiIds           ids to access api url (retrieved by apiTag), same order of appearance as in config.api[apiTag]
        *
        * @constructs
        * @see http://backbonejs.org/#Collection
        */
        initialize: function (models, options) {
            //_.bindAll(this, 'model');
            this.baseurl = options.url;
            this.apiTag = options.apiTag;
            this.apiIds = options.apiIds;
        },
        
        model: GDSEModel
    });

    return GDSECollection;
}
);