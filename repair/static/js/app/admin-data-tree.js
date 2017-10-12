define([
  'jquery',
  'treeview',
], function($, treeview) {

  var testTree = [
    {
      text: "P1: Production",
      data: "activity-group",
      nodes: [
        {
          text: "Manufacture of soft drinks",
          data: "activity",
          nodes: [
            {
              text: "Coca Cola",
              data: "actor"
            },
            {
              text: "Pepsi",
              data: "actor"
            }
          ]
        },
        {
          text: "Manufacture of juice",
          data: "activity",
          nodes: [
            {
              text: "something"
            }
          ]
        }
      ]
    },
    {
      text: "P2",
      data: "activity-group",
      nodes: [
        {
          text: "a child",
          data: "activity"
        },
      ]
    },
    {
      text: "P3",
      data: "activity-group"
    }
  ];
  $('#data-tree').treeview({data: testTree, showTags: true});
  
});