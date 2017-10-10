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
      text: "stuff",
      nodes: [
        {
          text: "a child"
        },
      ]
    },
    {
      text: "other stuff"
    }
  ];
  $('#data-tree').treeview({data: testTree});
  
});