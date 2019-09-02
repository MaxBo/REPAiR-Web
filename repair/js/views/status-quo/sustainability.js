define(['views/common/baseview', 'pdfjs-dist', 'models/gdsemodel'],

function(BaseView, PDFJS, GDSEModel){
/**
*
* @author Christoph Franke
* @name module:views/SustainabilityView
* @augments module:views/BaseView
*/
var SustainabilityView = BaseView.extend(
    /** @lends module:views/SustainabilityView.prototype */
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
        SustainabilityView.__super__.initialize.apply(this, [options]);
        var _this = this;

        this.caseStudy = options.caseStudy;
        this.mode = options.mode || 0;
        this.keyflow = options.keyflow;
        this.scale = 1;

        this.fileAttr = options.fileAttr;
        this.render();
    },

    /*
    * dom events (managed by jquery)
    */
    events: {
        'change #sustainability-file-input': 'showFilePreview',
        'click #prev': 'prevPage',
        'click #next': 'nextPage',
        'click .fullscreen-toggle': 'toggleFullscreen',
        'click #upload-sustainability-file': 'uploadFile'
    },

    /*
    * render the view
    */
    render: function(){
        SustainabilityView.__super__.render.call(this);
        var _this = this;
        this.canvas = this.el.querySelector("canvas");
        this.canvasWrapper = this.el.querySelector('#canvas-wrapper');
        this.pageStatus = this.el.querySelector('#page-status');
        this.pdfInput =  this.el.querySelector('#sustainability-file-input');
        var url = this.keyflow.get(this.fileAttr);
        if (url) {
            this.loader.activate();
            PDFJS.getDocument({url: url}).then(function(pdf) {
                _this.pdfDocument = pdf;
                _this.pageNumber = 1;
                _this.renderPage(_this.pageNumber);
                _this.loader.deactivate();
            });
        }
    },

    showFilePreview: function(event){
        var input = event.target,
            _this = this;
        if (input.files && input.files[0]){
            var reader = new FileReader();
            reader.onload = function (e) {
                _this.pageNumber = 1;
                var typedarray = new Uint8Array(e.target.result);
                _this.pdfDocument = null;
                PDFJS.getDocument(typedarray).then(function(pdf) {
                    _this.pdfDocument = pdf;
                    _this.renderPage(_this.pageNumber);
                });
            };
            reader.readAsArrayBuffer(input.files[0]);
        }
    },

    renderPage: function(number){
        this.canvasWrapper.style.display = 'block';
        if (!this.pdfDocument) return;
        var _this = this;
        this.pageRendering = true;
        this.pdfDocument.getPage(number).then(function(page) {
            var viewport = page.getViewport(_this.scale),
                ctx = _this.canvas.getContext('2d');
            _this.canvas.height = viewport.height;
            _this.canvas.width = viewport.width;

            var renderTask = page.render({
                canvasContext: _this.canvas.getContext('2d'),
                viewport: viewport
            });

            // wait for rendering to finish
            renderTask.promise.then(function() {
                _this.pageRendering = false;
                _this.pageStatus.innerHTML = number + '/' + _this.pdfDocument.numPages;

                if (_this.pageNumPending != null) {
                    _this.renderPage(_this.pageNumPending);
                    _this.pageNumPending = null;
                }
            });
        });
    },

    queueRenderPage: function(number) {
        if (this.pageRendering) {
            this.pageNumPending = number;
        } else {
            this.renderPage(number);
        }
    },

    prevPage: function() {
        if (this.pageNumber <= 1) return;
        this.pageNumber--;
        this.queueRenderPage(this.pageNumber);
    },

    nextPage: function() {
        if (this.pageNumber >= this.pdfDocument.numPages) return;
        this.pageNumber++;
        this.queueRenderPage(this.pageNumber);
    },

    toggleFullscreen: function(){
        this.canvasWrapper.classList.toggle('fullscreen');
        this.scale = this.canvasWrapper.classList.contains('fullscreen') ? 1.5 : 1;
        this.renderPage(this.pageNumber);
    },

    uploadFile: function(){
        var _this = this;

        if (this.pdfInput.files && this.pdfInput.files[0]){
            var pdf = this.pdfInput.files[0],
                data = {};
            data[this.fileAttr] = pdf;
            console.log(data)
            //this.keyflow.set('sustainability_conclusions', pdf);
            this.keyflow.save(data, {
                success: function () {
                    _this.alert(gettext('Upload successful'), gettext('Success'));
                },
                error: _this.onError,
                patch: true
            });
        }

        else {
            this.alert(gettext('No file selected. Canceling upload...'))
        }
    }

});
return SustainabilityView;
}
);
