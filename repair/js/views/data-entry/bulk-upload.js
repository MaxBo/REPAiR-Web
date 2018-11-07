
define(['views/common/baseview', 'underscore'],
function(BaseView, _){

/**
    *
    * @author Christoph Franke
    * @name module:views/BulkUploadView
    * @augments module:views/BaseView
    */
var BulkUploadView = BaseView.extend(
    /** @lends module:views/BulkUploadView.prototype */
    {

    /**
    * render view for bulk uploading keyflow data
    *
    * @constructs
    * @see http://backbonejs.org/#View
    */
    initialize: function(options){
        BulkUploadView.__super__.initialize.apply(this, [options]);
        this.render();
    },

    /*
    * dom events (managed by jquery)
    */
    events: {
    },


});
return BulkUploadView;
}
);
