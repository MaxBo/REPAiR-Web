define([
  'jquery',
  'treeview',
], function($, treeview) {

  var testTree = [
    {
      text: "P1: Production",
      nodes: [
        {
          text: "Manufacture of soft drinks",
          nodes: [
            {
              text: "Coca Cola"
            },
            {
              text: "Pepsi"
            }
          ]
        },
        {
          text: "Manufacture of juice",
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
      nodes: [
        {
          text: "a child"
        },
      ]
    },
    {
      text: "P3"
    }
  ];
  $('#data-tree').treeview({data: testTree});
  
});