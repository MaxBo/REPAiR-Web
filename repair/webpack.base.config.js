var path = require('path');
var webpack = require('webpack'),
    BundleTracker = require('webpack-bundle-tracker'),
    ExtractTextPlugin = require("extract-text-webpack-plugin");

module.exports = {
  context: __dirname,
  entry: {
    DataEntry: './js/data-entry',
    StudyArea: './js/study-area',
    StatusQuo: './js/status-quo',
    Changes:   './js/changes',
    Base:      './js/base',
  },
  
  output: {
    path: path.resolve('./repair/static/bundles/local/'),
    publicPath: '/static/bundles/local/',
    filename: "[name]-[hash].js"
  },

  plugins: [
    new webpack.optimize.CommonsChunkPlugin({ name: 'vendors', filename: 'vendors.js' }),
    new ExtractTextPlugin('style.css')
  ],
  
  node: { fs: 'empty', net: 'empty', tls: 'empty', child_process: 'empty', __filename: true, __dirname: true }, 
  
  externals: [ 'ws' ],
  
  module: {
    rules: [
      { 
        test: require.resolve("jquery"), 
        loader: 'expose-loader?jQuery!expose-loader?$' 
      },
      {
        test: /\.css$/,
        use: ExtractTextPlugin.extract({
          fallback: "style-loader",
          use: "css-loader"
        })
      },
      { 
        test: /\.(png|woff|woff2|eot|ttf|svg)$/, 
        loader: 'url-loader?limit=100000' 
      }
    ],
  },

  resolve: {
    modules : ['js', 'node_modules', 'bower_components'],
    alias: {
      'static': path.resolve('./repair/static'),
      'spatialsankey': 'libs/spatialsankey',
      'cyclesankey': 'libs/cycle-sankey',
      jquery: "jquery/src/jquery"
    },
    plugins: [
      new webpack.ProvidePlugin({
        _: 'loadash',
        d3: 'd3',
        $: "jquery",
        jQuery: "jquery"
      }),
    ]
  },
}

