define(['views/common/baseview', 'underscore', 'collections/gdsecollection',
        'summernote', 'summernote/dist/summernote.css'],

function(BaseView, _, GDSECollection, summernote){
/**
*
* @author Christoph Franke
* @name module:views/KeyflowsView
* @augments module:views/BaseView
*/
var KeyflowsView = BaseView.extend(
    /** @lends module:views/KeyflowsView.prototype */
    {

    /**
    * render view on keyflows in casestudy
    *
    * @param {Object} options
    * @param {HTMLElement} options.el                          element the view will be rendered in
    * @param {string} options.template                         id of the script element containing the underscore template to render this view
    * @param {Number} [options.mode=0]                         workshop (0, default) or setup mode (1)
    * @param {module:models/CaseStudy} options.caseStudy       the casestudy of the keyflows
    *
    * @constructs
    * @see http://backbonejs.org/#View
    */
    initialize: function(options){
        KeyflowsView.__super__.initialize.apply(this, [options]);
        var _this = this;

        this.template = options.template;
        this.caseStudy = options.caseStudy;
        var caseStudyId = this.caseStudy.id;

        this.mode = options.mode || 0;

        this.keyflows = new GDSECollection([], {
            apiTag: 'keyflowsInCaseStudy',
            apiIds: [ caseStudyId ]
        });

        this.keyflows.fetch({
            success: _this.render,
            error: _this.onError
        });

        this.editors = {};

    },

    /*
    * dom events (managed by jquery)
    */
    events: {
        'click .upload-keyflow-description': 'uploadEvent'
    },

    /*
    * render the view
    */
    render: function(){
        var _this = this,
            html = document.getElementById(this.template).innerHTML,
            template = _.template(html);
        this.el.innerHTML = template({ keyflows: this.keyflows });

        this.keyflows.forEach(function(keyflow){
            var row = document.createElement('div'),
                title = document.createElement('h3');
            row.classList.add('row', 'bordered');
            title.innerHTML = keyflow.get('name');
            title.style.float = 'left';
            row.style.marginBottom = '20px';
            row.appendChild(title);
            _this.el.appendChild(row);
            // render editor only in setup mode
            if (_this.mode === 1) _this.addEditor(row, keyflow);
            else _this.addView(row, keyflow);
        })

        var popovers = this.el.querySelectorAll('[data-toggle="popover"]');
        $(popovers).popover({ trigger: "focus" });
    },

    addEditor: function(el, keyflow){
        var _this = this,
            editor = document.createElement('div'),
            uploadBtn = document.createElement('button'),
            br = document.createElement('br'),
            icon = document.createElement('span');
        uploadBtn.classList.add('btn', 'btn-primary');
        uploadBtn.innerHTML = gettext('Upload');
        uploadBtn.style.float = 'left';
        uploadBtn.style.margin = '15px';
        icon.classList.add('glyphicon', 'glyphicon-upload');
        icon.style.float = 'left';
        icon.style.marginRight = '5px';
        br.style.clear = 'both';

        uploadBtn.appendChild(icon);
        el.appendChild(uploadBtn);
        el.appendChild(br);
        el.appendChild(editor);

        $(editor).summernote({
            height: 300,
            maxHeight: null,
            //tooltip: false
        });
        $(editor).summernote('code', keyflow.get('note'));

        uploadBtn.addEventListener('click', function(){
            var markup = $(editor).summernote('code');
            keyflow.save({ note: markup }, {
                success: function(){
                    _this.alert(gettext('Upload successful'), gettext('Success'));
                },
                error: _this.onError,
                patch: true
            });
        })
    },

    addView: function(el, keyflow){
        var view = document.createElement('div');
        el.appendChild(view);
        view.innerHTML = keyflow.get('note');
        view.style.clear = 'both';
    }

});
return KeyflowsView;
}
);
