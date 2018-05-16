define(["backbone", "app-config"],

function(Backbone, config) {

    /**
    *
    * @author Christoph Franke
    * @name module:models/GDSEModel
    * @augments Backbone.Model
    */
    var GDSEModel = Backbone.Model.extend(
        /** @lends module:models/GDSEModel.prototype */
        {
        idAttribute: "id",

        /**
            * generates an url to the api resource based on the ids given in constructor
            *
            * @returns {string} the url string
            */
        urlRoot: function(){
            // if concrete url was passed: take this and ignore the rest
            if (this.baseurl) return this.baseurl;

            // take url from api by tag and put the required ids in
            var apiUrl = config.api[this.apiTag]
            if (this.apiIds != null && this.apiIds.length > 0)
                apiUrl = apiUrl.format(...this.apiIds);
            return apiUrl;
        },

        /**
        * model for fetching/putting an activitygroup
        *
        * @param {Object} [attributes=null]          fields of the model and their values, will be set if passed
        * @param {Object} options
        * @param {string} options.baseurl          static url (overrides all of the follwing api arguments)
        * @param {string} options.apiTag           key of url as in config.api
        * @param {string} options.apiIds           ids to access api url (retrieved by apiTag), same order of appearance as in config.api[apiTag]
        *
        * @constructs
        * @see http://backbonejs.org/#Model
        */
        initialize: function (attributes, options) {
            //_.bindAll(this, 'model');
            this.baseurl = options.url;
            this.apiTag = options.apiTag;
            this.apiIds = options.apiIds;
        },

    });
    return GDSEModel;
}
);