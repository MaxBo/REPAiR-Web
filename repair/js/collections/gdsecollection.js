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
            var apiUrl = config.api[this.apiTag];
            if (this.apiIds != null && this.apiIds.length > 0)
                apiUrl = apiUrl.format(...this.apiIds);
            return apiUrl;
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
        * @param {Object} attributes         key/value pairs of attribute names and the values to match; value may be an array (any of elements may match to return true for single attribute)
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
                    var value = model.get(key),
                        checkValue = attributes[key];
                    if (Array.isArray(checkValue)){
                        for (var i = 0; i < checkValue.length; i++){
                            if (String(value) == String(checkValue[i])) return true;
                        }
                        return false;
                    }
                    return String(value) == String(checkValue);
                }
                if (options.operator == '||')
                    return keys.some(match)
                // &&
                return keys.every(match)
            });
            var ret = new this.__proto__.constructor(filtered,
                {
                    apiTag: this.apiTag,
                    apiIds: this.apiIds,
                    comparator: this.comparatorAttr
                }
            );
            return ret;
        },

        /**
        * fetch the collection with post data
        * use this function if a parameter is too big to be send as a query parameter
        * options accepts success and error functions same way as default Collection
        * WARNING: does not work well with pagination yet, use a huge page size to fetch all models at once
        *
        * @param {Object=} options
        * @param {Object=} options.body  request parameters to be put into the request body
        * @param {Object=} options.data  request parameters to be put into the url as query parameters
        *
        */
        postfetch: function (options){
            options = options ? _.clone(options) : {};
            if (options.parse === void 0) options.parse = true;
            var success = options.success;
            var collection = this;
            var queryData = options.data || {},
                success = options.success,
                _this = this;
            // move body attribute to post data (will be put in body by AJAX)
            // backbone does some strange parsing of nested objects
            var data = {};
            for (var key in options.body) {
                var value = options.body[key];
                data[key] = (value instanceof Object) ? JSON.stringify(value) : value;
            }
            options.data = data;

            // response to models on success, call passed success function
            function onSuccess(response){
                var method = options.reset ? 'reset' : 'set';
                collection[method](response, options);
                if (success) success.call(options.context, _this, response, options);
                _this.trigger('sync', _this, response, options);
            }

            options.success = onSuccess;
            // unfortunately PageableCollection has no seperate function to build
            // query parameters for pagination (all done in fetch())
            // ToDo: set page somehow
            queryData[this.queryParams.page || 'page'] = 1;
            queryData[this.queryParams.pageSize || 'page_size'] = this.state.pageSize;

            // GDSE API specific: signal the API that resources are requested
            // via POST method
            queryData.GET = true;

            return Backbone.ajax(_.extend({
                // jquery post does not automatically set the query params
                url: this.url() + '?' + $.param(queryData),
                method: "POST",
                dataType: "json",
            }, options));
        },

        // parameter names as used in the rest API
        queryParams: {
            pageSize: "page_size"
        },

        // called immediately after fetching, parses the response (json)
        parseRecords: function (response) {
            // paginated api urls return the models under the key 'results'
            if (response.results){
                this.count = response['count'];
                return response.results;
            }
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
            var options = options || {};
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
