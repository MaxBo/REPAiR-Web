define(['backbone', 'underscore', 'utils/utils'],
function(Backbone, _, utils){
/**
*
* @author Christoph Franke
* @name module:views/BaseView
* @augments Backbone.View
*/
var BaseView = Backbone.View.extend(
    /** @lends module:views/BaseView.prototype */
    {
    
    /**
    * Basic View with common functions, may be extended by other views
    *
    * @param {Object} options
    * @param {HTMLElement} options.el                   element the view will be rendered in (Backbone.View parameter)
    * @param {string} options.template                  id of the script element containing the underscore template to render this view
    * @param {Backbone.Model=} options.model            (Backbone.View parameter)
    * @param {Backbone.Collection=} options.collection  (Backbone.View parameter)
    *
    * @constructs
    * @see http://backbonejs.org/#View
    */
    initialize: function(options){
        _.bindAll(this, 'render');
        _.bindAll(this, 'alert');
        _.bindAll(this, 'onError');
        var _this = this;
        this.template = options.template;
    },
    
    /**
    * DOM events (jQuery style)
    */
    events: {
    },

    /**
    * render the view with template into element
    */
    render: function(){
        var html = document.getElementById(this.template).innerHTML,
            template = _.template(html);
        this.el.innerHTML = template();
    },

    /**
    * callback for selecting items in the hierarchical select
    *
    * @callback module:views/BaseView~onSelect
    * @param {Backbone.Model} model  the selected model
    */

    /**
    * build a hierarchical selection of a collection, the collection has to be 
    * of tree structure where the parents of a child are referenced by an attribute (options.parentAttr)
    * absence of parent indicates a root item
    *
    * @param {Backbone.Collection} collection       models of collection will be the items of the hierarchical select
    * @param {HTMLElement}                          the element to append the rendered hierarchical select to
    * @param {String} [options.parentAttr='parent'] the name of attribute referencing the id of the parent model
    * @param {module:views/BaseView~onSelect=} options.onSelect  function is called on selection of an item
    * @param {Number=} options.selected             preselects the model with given id 
    */
    hierarchicalSelect: function(collection, parent, options){

        var wrapper = document.createElement("div"),
            options = options || {},
            parentAttr = options.parentAttr || 'parent',
            defaultOption = options.defaultOption || 'All',
            items = [];

        // make a list out of the collection that is understandable by treeify and hierarchySelect
        collection.each(function(model){
            var item = {};
            var name = model.get('name');
            item.text = name.substring(0, 70);
            if (name.length > 70) item.text += '...';
            item.title = model.get('name');
            item.level = 1;
            item.id = model.id;
            item.parent = model.get(parentAttr);
            item.value = model.id;
            items.push(item);
        })

        var treeList = utils.treeify(items);

        // converts tree to list sorted by appearance in tree, 
        // stores the level inside the tree as an attribute in each node
        function treeToLevelList(root, level){
            var children = root['nodes'] || [];
            children = children.slice();
            delete root['nodes'];
            root.level = level;
            list = [root];
            children.forEach(function(child){
                list = list.concat(treeToLevelList(child, level + 1));
            })
            return list;
        };

        var levelList = [];
        treeList.forEach(function(root){ levelList = levelList.concat(treeToLevelList(root, 1)) });

        // load template and initialize the hierarchySelect plugin
        var inner = document.getElementById('hierarchical-select-template').innerHTML,
            template = _.template(inner),
            html = template({ options: levelList, defaultOption: defaultOption });
        wrapper.innerHTML = html;
        wrapper.name = 'material';
        parent.appendChild(wrapper);
        require('hierarchy-select');
        var select = wrapper.querySelector('.hierarchy-select');
        $(select).hierarchySelect({
            width: 400
        });

        // preselect an item
        if (options.selected){
            var selection = select.querySelector('.selected-label');
            var model = collection.get(options.selected);
            if (model){
                // unselect the default value
                var li = select.querySelector('li[data-default-selected]');
                li.classList.remove('active');
                selection.innerHTML = model.get('name');
                var li = select.querySelector('li[data-value="' + options.selected + '"]');
                li.classList.add('active');
            }
        }

        // event click on item
        var anchors = select.querySelectorAll('a');
        for (var i = 0; i < anchors.length; i++) {
            anchors[i].addEventListener('click', function(){
                var item = this.parentElement;
                var model = collection.get(item.getAttribute('data-value'));
                wrapper.title = item.title;
                if (options.onSelect) options.onSelect(model);
            })
        }
    },
    
    /**
    * show a modal with given alert message
    *
    * @param {String} message           html formatted message to show
    * @param {String} [title='Warning'] title displayed in header of modal
    */
    alert: function(message, title){
        var title = title || gettext('Warning');
        var el = document.getElementById('alert-modal'),
            html = document.getElementById('alert-modal-template').innerHTML,
            template = _.template(html);
        
        el.innerHTML = template({ title: title, message: message });
        $(el).modal('show'); 
    },
    
    /**
    * show a modal with error message on server error
    *
    * @param {Object} response    AJAX response
    */
    onError: function(response){
        var message = response.responseText;
        message = message ? '<b>' + gettext('The server responded with: ') + '</b><br>' + '<i>' + response.responseText + '</i>': 
                  gettext('Server does not respond.');
        this.alert(message, gettext('Error'));
    },
    
    /**
    * callback for confirming user input of name
    *
    * @callback module:views/BaseView~onNameConfirm
    * @param {String} name  the user input
    */
    
    /**
    * show a modal to enter a name
    *
    * @param {Object=} options
    * @param {module:views/BaseView~onNameConfirm} options.onConfirm  called when user confirms input
    */
    getName: function(options){
      
      var options = options || {};
      
      var el = document.getElementById('generic-modal'),
          inner = document.getElementById('empty-modal-template').innerHTML;
          template = _.template(inner),
          html = template({ header:  options.title || 'Name' });
      
      el.innerHTML = html;
      var body = el.querySelector('.modal-body');
      
      var row = document.createElement('div');
      row.classList.add('row');
      var label = document.createElement('div');
      label.innerHTML = gettext('Name');
      var input = document.createElement('input');
      input.style.width = '100%';
      input.value = options.name || '';
      body.appendChild(row);
      row.appendChild(label);
      row.appendChild(input);
      
      el.querySelector('.confirm').addEventListener('click', function(){
        if (options.onConfirm) options.onConfirm(input.value);
        $(el).modal('hide');
      });
      
      $(el).modal('show');
    },

    /**
    * unbind the events and remove this view from the DOM and 
    */
    close: function(){
        this.undelegateEvents(); // remove click events
        this.unbind(); // Unbind all local event bindings
        this.el.innerHTML = ''; //empty the DOM element
    }

});
return BaseView;
}
);