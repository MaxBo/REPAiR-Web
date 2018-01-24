var path = require('path');
var webpack = require('webpack');
var BundleTracker = require('webpack-bundle-tracker');

module.exports = {
  context: __dirname,
  entry: {
    DataEntry: './js/data-entry',
    StudyArea: './js/study-area',
    StatusQuo: './js/status-quo',
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
  
  module: {
    rules: [{ test: require.resolve("jquery"), loader: 'expose-loader?jQuery!expose-loader?$' }] 
  },

  resolve: {
    modules : ['js', 'node_modules', 'bower_components'],
      alias: {
        'spatialsankey': 'libs/spatialsankey',
        jquery: "jquery/src/jquery"
      },
    plugins: [
      new webpack.ProvidePlugin({
        _: 'loadash',
        d3: 'd3',
        $: "jquery",
        jQuery: "jquery"
      })
    ]
  },
}

