define(["models/gdsemodel", "app-config"],

function(GDSEModel, config) {

    var Indicator = GDSEModel.extend({

        /**
        * set the geometry of the location
        *
        * @param {Array.<number>} coordinates  (x, y) coordinates
        * @param {string} [type='Point']     type of geometry
        *
        * @see http://backbonejs.org/#Model
        */
        compute: function(options){
            var url = this.url() + '/compute';
            
            Backbone.ajax({
                url: url,
                data: options.data,
                success: options.success,
                error: options.error
            });
        }
    });
    return Indicator
}
);