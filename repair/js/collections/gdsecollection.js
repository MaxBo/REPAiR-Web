define(["backbone-pageable", "underscore", "models/gdsemodel", "app-config"],

function(PageableCollection, _, GDSEModel, config) {

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
        * generates the url based on the passed options when initializing
        *
        * @returns {string} the url string
        */
        url: function(){
            // if concrete url was passed: take this and ignore the rest
            if (this.baseurl) return this.baseurl;
            
            // take url from api by tag and put the required ids in
            var apiUrl = config.api[this.apiTag]
            if (this.apiIds != null && this.apiIds.length > 0)
                apiUrl = apiUrl.format(...this.apiIds);
            return apiUrl
        },
        
        // by default try to fetch 'em all (should never exceed 1Mio hopefully)
        // you may reduce the pageSize to get real paginated results
        state: {
            pageSize: 1000000,
            firstPage: 1,
            currentPage: 1
        },

        /**
        * filter the collection by its attributes
        * the values to each attribute have to be an exact (by default) match to add a model to the returned results
        *
        * @param {Object} attributes         key/value pairs of attribute names and the values to match
        * @param {Object=} options
        * @param {String} [options.operator='&&']  the logical function to connect the attribute checks, by default all given attributes have to match, optional: '||'
        *
        * @returns {Array.<Backbone.model>}  list of all models matching the passed attribute/value combinations
        */
        filterBy: function (attributes, options) {
            var options = options || {},
                keys = Object.keys(attributes);
            var filtered = this.filter(function (model) {
                function match(key){
                    return String(model.get(key)) == String(attributes[key])
                }
                if (options.operator == '||') 
                    return keys.some(match)
                // &&
                return keys.every(match)
            });
            return filtered;
        },

        // parameter names as used in the rest API
        queryParams: {
            pageSize: "page_size"
        },
        
        // called immediately after fetching, parses the response (json)
        parseRecords: function (response) {
            // paginated api urls return the models under the key 'results'
            if (response.results)
                return response.results;
            return response;
        },
        
        // function to compare models by the preset attribute (id per default) whenever you call sort 
        comparator: function(model) {
          return model.get(this.comparatorAttr);
        },

        /**
        * generic collection collection matching most of the GDSE backend api
        *
        * @param {Array.<Backbone.model>} models   list objects representing the fields of each model and their values, will be set if passed
        * @param {Object} options
        * @param {string} options.baseurl          static url (overrides all of the follwing api arguments)
        * @param {string} options.apiTag           key of url as in config.api
        * @param {string} options.apiIds           ids to access api url (retrieved by apiTag), same order of appearance as in config.api[apiTag]
        * @param {string} [options.comparator='id'] attribute used for sorting
        *
        * @constructs
        * @see http://backbonejs.org/#Collection
        */
        initialize: function (models, options) {
            //_.bindAll(this, 'model');
            this.baseurl = options.url;
            this.apiTag = options.apiTag;
            this.apiIds = options.apiIds || options.apiIDs; // me (the author) tends to mix up both notations of 'Id' randomly and confuses himself by that
            this.comparatorAttr = options.comparator || 'id';
        },
        
        model: GDSEModel
    });

    return GDSECollection;
}
);