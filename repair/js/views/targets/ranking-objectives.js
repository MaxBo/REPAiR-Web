
define(['underscore','views/common/baseview', 'collections/gdsecollection',
        'muuri'],

function(_, BaseView, GDSECollection, Muuri){
    /**
    *
    * @author Christoph Franke
    * @name module:views/RankingObjectivesView
    * @augments Backbone.View
    */
    var RankingObjectivesView = BaseView.extend(
        /** @lends module:views/RankingObjectivesView.prototype */
        {

        /**
        * render workshop view on ranking the objectives in a keyflow
        *
        * @param {Object} options
        * @param {HTMLElement} options.el                      element the view will be rendered in
        * @param {string} options.template                     id of the script element containing the underscore template to render this view
        * @param {module:models/CaseStudy} options.caseStudy   the casestudy of the keyflow
        * @param {module:models/CaseStudy} options.keyflowId   the keyflow the objectives belong to
        *
        * @constructs
        * @see http://backbonejs.org/#View
        */
        initialize: function(options){
            RankingObjectivesView.__super__.initialize.apply(this, [options]);
            var _this = this;
            _.bindAll(this, 'renderObjective');

            this.template = options.template;
            this.caseStudy = options.caseStudy;
            this.keyflowId = options.keyflowId;
            this.keyflowName = options.keyflowName;
            this.userObjectives = options.userObjectives;
            this.aims = options.aims;

            this.render();
        },

        /*
        * dom events (managed by jquery)
        */
        events: {
            'click .add-target': 'addTarget'
        },

        /*
        * render the view
        */
        render: function(){
            var _this = this,
                html = document.getElementById(this.template).innerHTML,
                template = _.template(html);
            this.el.innerHTML = template({ keyflowName: this.keyflowName });
            var panel = this.el.querySelector('.item-panel');
            this.grid = new Muuri(panel, {
                items: '.panel-item',
                dragAxis: 'y',
                layoutDuration: 400,
                layoutEasing: 'ease',
                dragEnabled: true,
                dragSortInterval: 0,
                dragReleaseDuration: 400,
                dragReleaseEasing: 'ease'
            });

            this.grid.on('dragReleaseEnd', function(item) {
                var id = item.getElement().dataset['id'];
                _this.uploadPriorities(id);
            });
            // render objectives with set priorities on top
            this.userObjectives.forEach(function(objective){
                if (objective.get('priority') >= 0)
                    _this.renderObjective(objective)
            });
            this.userObjectives.forEach(function(objective){
                if (objective.get('priority') < 0)
                    _this.renderObjective(objective)
            });

            var btns = this.el.querySelectorAll('button');
            _.each(btns, function(button){
                button.style.display = 'none';
            });
        },

        renderObjective: function(objective){
            var html = document.getElementById('panel-item-template').innerHTML,
                template = _.template(html),
                panelItem = document.createElement('div'),
                itemContent = document.createElement('div'),
                rankDiv = document.createElement('div'),
                priority = objective.get('priority'),
                _this = this;
            var aim = this.aims.get(objective.get('aim'));
            panelItem.classList.add('panel-item');
            panelItem.classList.add('draggable');
            panelItem.style.position = 'absolute';
            panelItem.dataset.id = objective.id;
            itemContent.classList.add('noselect', 'item-content');
            itemContent.innerHTML = template({ name: aim.get('text') });
            panelItem.appendChild(itemContent);
            this.grid.add(panelItem);

            panelItem.querySelector('.item-content').append(rankDiv)
            if (priority < 1)
                panelItem.style.background = '#d1d1d1';
            else {
                var overlay = panelItem.querySelector('.overlay');
                overlay.style.display = 'inline-block';
                overlay.innerHTML = priority;
            }
        },

        uploadPriorities: function(draggedId){
            var items = this.grid.getItems(),
                priority = 1,
                _this = this;
            items.forEach(function(item){
                var el = item.getElement(),
                    id = el.dataset.id,
                    objective = _this.userObjectives.get(id);
                // only update priorities for the dragged item and those whose
                // priority was assigned before
                if (draggedId == id || parseInt(objective.get('priority')) >= 1) {
                    el.style.background = null;
                    objective.set('priority', priority);
                    objective.save();
                    var overlay = el.querySelector('.overlay');
                    overlay.style.display = 'inline-block';
                    overlay.innerHTML = priority;
                    priority++;
                }
            })
        }

    });
    return RankingObjectivesView;
}
);
