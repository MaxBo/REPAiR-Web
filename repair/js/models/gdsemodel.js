define(["backbone", "utils/utils", "app-config"],

function(Backbone, utils, config) {

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
        * @param {string} options.fileAttributes   names of the attributes that should be uploaded as files
        *
        * @constructs
        * @see http://backbonejs.org/#Model
        */
        initialize: function (attributes, options) {
            var options = options || {};
            //_.bindAll(this, 'model');
            this.baseurl = options.url;
            this.apiTag = options.apiTag;
            this.apiIds = options.apiIds || options.apiIDs; // me (the author) tends to mix up both notations of 'Id' randomly and confuses himself by that
            this.fileAttributes = options.fileAttributes || [];
        },

        /**
        * overrides save function of Backbone models.
        * enables possibility to upload the model as a form instead of JSON, 
        * if attributes in data object are instances of File the model is automatically uploaded as a form (django needs it that way)
        *
        * WARNING: the changed attributes of model are ignored when uploading as form, only passed data will be put into form
        *
        * @param {Object} data       same as in Backbone.Model.save, values of file attributes have to be instances of File (the JS one)
        * @param {Object} options    same as in Backbone.Model.save
        * @param {Boolean} [options.uploadAsForm=false]  force uploading as form 
        *
        * @constructs
        * @see http://backbonejs.org/#Model
        */
        save: function(data, options){
            var _this = this,
                options = options || {},
                uploadAsForm = options.uploadAsForm || false,
                data = data || {};
            // check if one of the attributes is a file
            if (!uploadAsForm){
                for (key in data){
                    if (data[key] instanceof File ) {
                        uploadAsForm = true;
                        break;
                    }
                }
            }

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
            else return GDSEModel.__super__.save.apply(this, [data, options]);
    },

    });
    return GDSEModel;
}
);