var path = require("path")
var webpack = require('webpack')
var BundleTracker = require('webpack-bundle-tracker')
var config = require('./webpack.base.config.js')

var ip = 'localhost';
var port = '8001';

config.entry = {
    DataEntry: ['./repair/static/js/data-entry', 'webpack/hot/only-dev-server'],
    devServerClient: 'webpack-dev-server/client?http://0.0.0.0:' + port
    //vendors: './repair/static/bundles/local/vendors.js'
}

config.output.publicPath = 'http://' + ip + ':' + port + '/assets/bundles/'

config.devtool = "#eval-source-map";

config.plugins = config.plugins.concat([
  new webpack.HotModuleReplacementPlugin(),
  new webpack.NoEmitOnErrorsPlugin(),
  new BundleTracker({filename: './repair/webpack-stats-dev.json'}),
])
  
module.exports = config;