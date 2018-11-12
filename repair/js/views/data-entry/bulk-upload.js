
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
                ie, is = 0,
                u_msg = gettext('Removing data') + ' ' + tag;
            _this.log(u_msg);
            _this.log('-'.repeat(u_msg.length * 1.4));

            if (i === 0){
                _this.log('<p style="color: green;">' + gettext('Nothing to remove') + '</p>');
                _this.loader.deactivate();
                return;
            }
            function done(){
                var msg = '',
                    color = 'green';
                if (is > 0)
                    msg += is + ' ' + gettext('entries removed') + '  ';
                if (ie > 0){
                    msg += ie + ' ' + gettext('entries failed to remove');
                    color = 'red';
                }
                _this.log('<p style="color:' + color + ';">' + msg + '</p>')
                _this.loader.deactivate();
            }

            while (model = collection.first()) {
                model.destroy({
                    success: function(res){
                        var m_repr = JSON.stringify(res.toJSON());
                        msg = gettext('Successfully deleted') + ' ' + m_repr;
                        _this.log(msg)
                        i -= 1;
                        is += 1;
                        if (i < 1) done();
                    },
                    error: function(res){
                        msg = res.responseText;
                        _this.log('<p style="color: red;">' + msg + '</p>')
                        i -= 1;
                        ie += 1;
                        if (i < 1) done();
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
                var res = res.toJSON(),
                    updated = res.updated,
                    created = res.created;
                _this.log(gettext('Created models:'));
                if (created.length == 0) _this.log('-');
                created.forEach(function(m){
                    _this.log(JSON.stringify(m));
                })
                _this.log(gettext('Updated models:'));
                if (updated.length == 0) _this.log('-');
                updated.forEach(function(m){
                    _this.log(JSON.stringify(m));
                })
                var div = document.createElement('div'),
                    title = document.createElement('strong'),
                    msgWrapper = document.createElement('p');
                title.style.float = 'left';
                title.style.marginRight = '5px';
                title.innerHTML = gettext('Success') + '!';
                div.appendChild(title);
                div.appendChild(msgWrapper);

                msgWrapper.innerHTML = res.created.length + ' entries created, ' + res.updated.length + ' entries updated';
                _this.bootstrapAlert(div.innerHTML, {
                    parentEl: row,
                    type: 'success',
                    dismissible: true
                })
                msgWrapper.style.color = 'green';
                title.style.color = 'green';
                // that is not very elegant, but when adding a div to the alert
                // the close button is shifted
                alertDiv.querySelector('.close').style.top = '-20px';
                _this.log(div.innerHTML)
                _this.loader.deactivate()
            },
            error: function (res, r) {
                var div = document.createElement('div'),
                    title = document.createElement('strong'),
                    msgWrapper = document.createElement('p'),
                    msg;
                title.style.float = 'left';
                title.style.marginRight = '5px';
                title.innerHTML = gettext('Error') + '!';
                msgWrapper.style.float = 'left';
                msgWrapper.style.marginRight = '10px';
                div.appendChild(title);
                div.appendChild(msgWrapper);

                if (res.responseJSON){
                    msg = res.responseJSON.message;
                    var url = res.responseJSON.file_url;
                    if (url){
                        var download = _this.createDownloadIcon(url);
                        div.appendChild(download);
                    }
                }
                else
                    msg += res.responseText;

                msgWrapper.innerHTML = msg;

                var alertDiv = _this.bootstrapAlert(div.innerHTML, {
                    parentEl: row,
                    type: 'danger',
                    dismissible: true
                })
                alertDiv.querySelector('.close').style.top = '-20px';
                msgWrapper.style.color = 'red';
                title.style.color = 'red';
                _this.log(div.innerHTML)
                _this.loader.deactivate()
            },
        });
    },

    createDownloadIcon: function(url){
        var div = document.createElement('div'),
            span = document.createElement('span'),
            a = document.createElement('a');
        span.classList.add('fas', 'fa-save');
        span.style.float = 'left';
        span.style.marginRight = '5px';
        a.setAttribute('href', url);
        // ToDo: keep file ending
        a.setAttribute('download', 'error-response');
        a.innerHTML = gettext('Response');
        div.appendChild(a);
        a.appendChild(span);
        return div;
    }


});
return BulkUploadView;
}
);
