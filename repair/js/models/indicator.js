define(["models/gdsemodel", "app-config"],

function(GDSEModel, config) {

    var Indicator = GDSEModel.extend({

        /**
        * compute the indicator
        *
        * @param {Object} options
        * @param {Object} options.data  query parameters (GET) or body params (POST)
        * @param {string} [options.method='GET']  post or fetch for computation
        * @param {function} options.success  callback for success
        * @param {function} options.error  callback for error
        *
        * @author Christoph Franke
        */
        compute: function(options){
            var url = this.url() + '/compute/',
                options = options || {};

            Backbone.ajax({
                url: url,
                method: options.method || 'GET',
                data: options.data,
                success: options.success,
                error: options.error
            });
        }
    });
    return Indicator
}
);
