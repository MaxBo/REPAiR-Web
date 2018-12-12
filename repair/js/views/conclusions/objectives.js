
define(['underscore','views/common/baseview', 'collections/gdsecollection'],

function(_, BaseView, GDSECollection, Muuri){
    /**
    *
    * @author Christoph Franke
    * @name module:views/EvalObjectivesView
    * @augments Backbone.View
    */
    var EvalObjectivesView = BaseView.extend(
        /** @lends module:views/EvalObjectivesView.prototype */
    {

        /**
        * render workshop view on overall objective-ranking by involved users
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
            EvalObjectivesView.__super__.initialize.apply(this, [options]);
            var _this = this;
            this.template = options.template;
            this.caseStudy = options.caseStudy;
            this.aims = options.aims;
            this.objectives = options.objectives;
            this.keyflowId = options.keyflowId;
            this.keyflowName = options.keyflowName;
            this.users = options.users;

            this.render();
        },
        /*
        * render the view
        */
        render: function(){
            EvalObjectivesView.__super__.render.call(this);
            var _this = this;
            this.table = this.el.querySelector('#objectives-table');
            var header = this.table.createTHead().insertRow(0),
                fTh = document.createElement('th');
            fTh.innerHTML = gettext('Objectives for key flow <i>' + this.keyflowName + '</i>')
            header.appendChild(fTh);
            var rankingMap = {},
                userColumns = [],
                avgRankings = {};
            this.users.forEach(function(user){
                var name = user.get('alias') || user.get('name'),
                    th = document.createElement('th');
                userColumns.push(user.id);
                th.innerHTML = name;
                header.appendChild(th);
                var userObjectives = _this.objectives.filterBy({'user': user.get('user')});
                userObjectives.comparator = 'priority';
                userObjectives.sort();
                // normalize priorities into a ranking from 1 ascending
                var i = 1;
                userObjectives.forEach(function(userObj){
                    var aimId = userObj.get('aim'),
                        aimRank = rankingMap[aimId];
                    // aim was not considered yet
                    if (!aimRank) {
                        aimRank = rankingMap[aimId] = {};
                        avgRankings[aimId] = 0;
                    }
                    aimRank[user.id] = i;
                    avgRankings[aimId] += i;
                    i++;
                })
            })

            // sort aims by average ranking
            var sortRank = [];
            for (var aimId in avgRankings) {
                sortRank.push([aimId, avgRankings[aimId]]);
            }
            sortRank.sort(function(a, b) {
                return a[1] - b[1];
            });

            var colorStep = 70 / sortRank.length;

            // fill table with sorted aims and individual ranks
            var i = 1;
            sortRank.forEach(function(sortedAim){
                var aim = _this.aims.get(sortedAim[0]),
                    row = _this.table.insertRow(-1),
                    item = _this.createAimItem(aim, i);
                row.insertCell(0).appendChild(item);
                var aimRank = rankingMap[aim.id];
                userColumns.forEach(function(userId){
                    var cell = row.insertCell(-1),
                        rank = aimRank[userId];
                    if (rank) {
                        var item = _this.panelItem('#' + rank);
                        item.style.width = '50px';
                        cell.appendChild(item);
                        var sat = 30 + colorStep * (rank -1),
                            hsl = 'hsla(90, 50%, ' + sat + '%, 1)';
                        if (sat < 50) item.style.color = 'white';
                        item.style.backgroundColor = hsl;
                    }
                });
                i++;
            })
        },

        createAimItem: function(aim, rank){
            var desc = aim.get('description') || '';

            var panelItem = this.panelItem(aim.get('text'), {
                popoverText: desc.replace(/\n/g, "<br/>"),
                overlayText: '#' + rank
            })
            panelItem.style.maxWidth = '500px';
            var overlay = panelItem.querySelector('.overlay');
            overlay.innerHTML = '#' + rank;
            // ToDo: put next lines into style sheet
            // adjust overlay offset, because parent div pos. is not absolute
            // move it left
            overlay.style.top = '-15px';
            overlay.style.left = '15px';
            overlay.style.right = 'auto';
            // make space for the overlay
            panelItem.querySelector('label').style.paddingLeft = '30px';
            return panelItem;
        },
    });
    return EvalObjectivesView;
}
);

