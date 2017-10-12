define([
  'jquery',
  'treeview',
], function($, treeview) {

  var DataTree = function(options){
    var divid = options.divid;
    var onClick = options.onClick;
    
    var testTree = [
      {
        text: "P1: Production",
        tag: "activity-group",
        nodes: [
          {
            text: "Manufacture of soft drinks",
            tag: "activity",
            nodes: [
              {
                text: "Coca Cola",
                tag: "actor"
              },
              {
                text: "Pepsi",
                tag: "actor"
              }
            ]
          },
          {
            text: "Manufacture of juice",
            tag: "activity",
            nodes: [
              {
                text: "something",
                tag: "activity"
              }
            ]
          }
        ]
      },
      {
        text: "P2",
        tag: "activity-group",
        nodes: [
          {
            text: "a child",
            tag: "activity"
          },
        ]
      },
      {
        text: "P3",
        tag: "activity-group"
      }
    ];
    $(divid).treeview({data: testTree, showTags: true});
    $(divid).on('nodeSelected', function(event, node) {
      onClick(node);
    });
  };
  return DataTree;
  
});