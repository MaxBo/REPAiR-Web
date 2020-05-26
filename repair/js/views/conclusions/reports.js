define(['views/common/baseview', 'underscore', 'pdfjs-dist',
        'collections/gdsecollection', 'models/gdsemodel'],

function(BaseView, _, PDFJS, GDSECollection, GDSEModel){
/**
*
* @author Christoph Franke
* @name module:views/ReportsView
* @augments module:views/BaseView
*/
var ReportsView = BaseView.extend(
    /** @lends module:views/ReportsView.prototype */
    {

    /**
    * render view to setup or show pdf report
    *
    * @param {Object} options
    * @param {HTMLElement} options.el                          element the view will be rendered in
    * @param {string} options.template                         id of the script element containing the underscore template to render this view
    * @param {Number} [options.mode=0]                         workshop (0, default) or setup mode (1)
    * @param {module:models/CaseStudy} options.caseStudy       the casestudy to add layers to
    *
    * @constructs
    * @see http://backbonejs.org/#View
    */
    initialize: function(options){
        ReportsView.__super__.initialize.apply(this, [options]);
        _.bindAll(this, 'renderPreviewItem');
        this.caseStudy = options.caseStudy;
        this.scale = 1;
        this.setupMode = options.setupMode;
        this.reports = options.reports;
        this.apiTag = this.reports.apiTag;
        this.render();
    },

    /*
    * dom events (managed by jquery)
    */
    events: {
        'click #add-report': 'addReport'
    },

    /*
    * render the view
    */
    render: function(){
        ReportsView.__super__.render.call(this);
        var _this = this;

        this.canvas = this.el.querySelector("canvas");
        this.canvasWrapper = this.el.querySelector('#canvas-wrapper');
        this.pageStatus = this.el.querySelector('#page-status');
        this.pdfInput =  this.el.querySelector('#sustainability-file-input');
        this.status = document.createElement('h3');
        this.el.appendChild(this.status);

        this.reports.forEach(this.renderPreviewItem);
    },

    renderPreviewItem: function(report){
        var html = document.getElementById('report-preview-item-template').innerHTML,
            item = document.createElement('div'),
            template = _.template(html),
            previews = this.el.querySelector('#report-previews'),
            _this = this;

        previews.style.maxHeight = 0.8 * window.outerHeight + 'px';
        item.classList.add('preview-item','shaded','bordered');
        item.innerHTML = template({ report: report });

        previews.appendChild(item);

        var img = item.querySelector('img');
        img.parentElement.addEventListener('click', function(){
            previews.querySelectorAll('.preview-item').forEach(function(item){
                item.classList.remove('selected');
            });
            item.classList.add('selected');
            _this.renderReport(report);
        })

        if (this.setupMode) {
            var editBtn = item.querySelector('.edit'),
                removeBtn = item.querySelector('.remove');
            console.log(report)
            editBtn.addEventListener('click', function(){
                _this.getName({
                    name: report.get('name'),
                    onConfirm: function(name){
                        report.save({ name: name }, {
                            success: function(){
                                item.querySelector('.title').innerHTML = name;
                            },
                            error: _this.onError,
                            patch: true
                        })
                    }
                })
            })
            removeBtn.addEventListener('click', function(){
                var message = gettext('Do you really want to delete the report?');
                _this.confirm({ message: message, onConfirm: function(){
                    if (report == _this.openedReport)
                        _this.el.querySelector('#pdf-viewer-content').innerHTML = '';
                    report.destroy({
                        success: function() {
                            previews.removeChild(item);
                        },
                        error: _this.onError,
                        wait: true
                    })
                }});
            })
        }
        return item;
    },

    addReport: function(){
        if (!this.setupMode) return;
        var _this = this;
        this.getInputs({
            title: gettext('Add report'),
            inputs: {
                name: {
                    type: 'text',
                    label: gettext('Name')
                },
                pdf: {
                    type: 'file',
                    label: gettext('PDF File'),
                    accept: 'application/pdf'
                }
            },
            onConfirm: function(obj){
                if (obj.pdf[0]){
                    var pdf = obj.pdf[0],
                        data = {};
                    var report = new GDSEModel( {}, {
                        apiTag: _this.apiTag,
                        apiIds: [ _this.caseStudy.id ]}
                    );
                    report.save({ report: pdf, name: obj.name }, {
                        success: function (report) {
                            _this.alert(gettext('Upload successful'), gettext('Success'));
                            _this.renderPreviewItem(report);
                        },
                        error: _this.onError
                    });
                }
                else {
                    _this.alert(gettext('No file selected. Canceling upload...'))
                }
            }
        })
    },

    renderReport: function(report){
        this.openedReport = report;
        var url = report.get('report'),
            iframe = document.createElement('iframe');
            content = this.el.querySelector('#pdf-viewer-content');
        content.innerHTML = '';
        iframe.src = '/pdfviewer/?file=' + url;
        content.appendChild(iframe);
        iframe.width = '100%';
        iframe.height = 0.8 * window.outerHeight;
    },

});
return ReportsView;
}
);
