var path = require("path")
var webpack = require('webpack')
var BundleTracker = require('webpack-bundle-tracker')
var config = require('./webpack.base.config.js')

var ip = 'localhost';
var port = '8001';

// assign hot reloading to all entry points
Object.keys(config.entry).forEach(function(key, index){
  var value = config.entry[key];
  config.entry[key] = [value, 'webpack/hot/only-dev-server']
});

config.entry.devServerClient = 'webpack-dev-server/client?http://' + ip + ':' + port;

config.output.path = path.resolve('./repair/static/bundles/dev/');
config.output.publicPath = 'http://' + ip + ':' + port + '/static/bundles/dev/';

config.devtool = "#eval-source-map";

config.plugins = config.plugins.concat([
  new webpack.HotModuleReplacementPlugin(),
  new webpack.NoEmitOnErrorsPlugin(),
  new BundleTracker({filename: './repair/webpack-stats-dev.json'}),
])
  
module.exports = config;