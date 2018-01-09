var path = require('path');
var webpack = require('webpack');
var BundleTracker = require('webpack-bundle-tracker');

module.exports = {
  context: __dirname,
  entry: {
    DataEntry: './repair/static/js/data-entry',
    //vendors: './repair/static/bundles/local/vendors.js'
  },
  
  output: {
    path: path.resolve('./repair/static/bundles/local/'),
    publicPath: '/static/bundles/local/',
    filename: "[name]-[hash].js"
  },

  plugins: [
    new webpack.optimize.CommonsChunkPlugin({ name: 'vendors', filename: 'vendors.js' }),
  ],
  
  node: { fs: 'empty', net: 'empty', tls: 'empty', child_process: 'empty', __filename: true, __dirname: true }, 
  
  externals: [ 'ws' ],
  //target: 'node',
  
  module: {
    //exprContextRegExp: /^\.\/.*$/,
    //unknownContextRegExp: /^\.\/.*$/,
    rules: [] // add all common loaders here
  },

  resolve: {
    modules : ['static/js', 'node_modules', 'bower_components'],
      alias: {
        //"treeview": "libs/bootstrap-treeview.min",
        'ol-contextmenu': 'libs/ol-contextmenu',
        'spatialsankey': 'libs/spatialsankey',
        //'tablesorter-widgets': 'libs/jquery.tablesorter.widgets',
        //'tablesorter-pager': 'libs/jquery.tablesorter.pager',
      },
    plugins: [
      new webpack.ProvidePlugin({
        _: 'loadash',
        d3: 'd3',
        $: "jquery",
        jQuery: "jquery"
      })
    ]
    //extensions: ['.js', '.jsx']
  },
}

