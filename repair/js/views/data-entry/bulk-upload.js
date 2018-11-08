
define(['views/common/baseview', 'underscore', 'models/gdsemodel', 'collections/gdsecollection'],
function(BaseView, _, GDSEModel, GDSECollection){

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
        this.caseStudy = options.caseStudy;
    },

    /*
    * dom events (managed by jquery)
    */
    events: {
        "click button.upload": "upload",
        "click #remove-keyflow": "removeKeyflow",
        "click button.clear": "clearData"
        //"click #clear-keyflow": "clearKeyflow"
    },

    render: function(){
        var html = document.getElementById(this.template).innerHTML,
            template = _.template(html);
        this.el.innerHTML = template({ keyflow: this.model });
        this.logArea = this.el.querySelector('#upload-log');
    },

    removeKeyflow: function(){
        var _this = this;
        function destroyKeyflow(){
            _this.model.destroy({
                success: function(){
                    document.querySelector('body').style.opacity=0.3;
                    location.reload();
                },
                error: _this.onError
            })
        }
        this.confirm({
            message: gettext('Do you really want to delete the keyflow and <b>ALL</b> of its data?'),
            onConfirm: function(){
                _this.confirm({
                        message: gettext('Are you sure?'),
                        onConfirm: destroyKeyflow
                    }
                )
            }
        })
    },

    clearData: function(evt){
        var _this = this,
            btn = evt.target,
            tag = btn.dataset['tag'];

        function destroyModels(collection){
            var i = collection.length,
                u_msg = gettext('Removing data') + ' ' + tag;
            _this.log(u_msg);
            _this.log('-'.repeat(u_msg.length * 1.4));

            if (i === 0){
                _this.log('<p style="color: green;">' + gettext('Nothing to remove') + '</p>');
                return;
            }

            while (model = collection.first()) {
                model.destroy({
                    success: function(res){
                        var m_repr = JSON.stringify(res.toJSON());
                        msg = gettext('Successfully deleted') + ' ' + m_repr;
                        _this.log(msg)
                        i -= 1;
                        if (i < 1) {
                            _this.loader.deactivate();
                        }
                    },
                    error: function(res){
                        msg = res.responseText;
                        _this.log('<p style="color: red;">' + msg + '</p>')
                        i -= 1;
                        if (i < 1) {
                            _this.loader.deactivate();
                        }
                    }
                });
            }
        }

        var collection = new GDSECollection( {}, {
            apiTag: tag, apiIds: [ this.caseStudy.id, this.model.id ]
        });

        this.confirm({
            message: gettext('Do you really want to delete the existing data and <b>ALL</b> of the related data?'),
            onConfirm: function(){
                _this.loader.activate();
                collection.fetch({
                    success: destroyModels,
                    error: _this.onError
                })
            }
        })
    },

    log: function(text){
        this.logArea.innerHTML += text + '<br>';
        this.logArea.scrollTop = this.logArea.scrollHeight;
    },

    upload: function(evt){
        var _this = this,
            btn = evt.target,
            tag = btn.dataset['tag'];

        var row = this.el.querySelector('.row[data-tag="' + tag +  '"]'),
            input = row.querySelector('input[type="file"]'),
            files = input.files;

        if (files.length === 0){
            this.alert(gettext('No file selected to upload!'));
            return;
        }

        var data = {
            'bulk_upload': files[0]
        }

        var model = new GDSEModel( {}, {
            apiTag: tag, apiIds: [ this.caseStudy.id, this.model.id ]
        });
        this.loader.activate();
        var u_msg = gettext('Uploading') + ' ' + files[0].name;
        this.log(u_msg);
        this.log('-'.repeat(u_msg.length * 1.4));
        model.save(data, {
            success: function (res) {
                var res = res.toJSON();
                res.results.forEach(function(m){
                    //if (m.url) delete m.url;
                    _this.log(JSON.stringify(m));
                })
                var msg = '<strong>' + gettext('Success') + '!</strong>&nbsp;' + res.added + ' entries added, ' + res.updated + ' entries updated';
                _this.bootstrapAlert(msg, {
                    parentEl: row,
                    type: 'success',
                    dismissible: true
                })
                _this.log('<p style="color: green;">' + msg +  '</p>')
                _this.loader.deactivate()
            },
            error: function (res, r) {
                var msg = res.responseJSON ? res.responseJSON.message: res.responseText;
                msg = '<strong>' + gettext('Error') + '!</strong>&nbsp;' + msg;
                _this.bootstrapAlert(msg, {
                    parentEl: row,
                    type: 'danger',
                    dismissible: true
                })
                _this.log('<p style="color: red;">' + msg + '</p>')
                _this.loader.deactivate()
            },
        });
    }


});
return BulkUploadView;
}
);
