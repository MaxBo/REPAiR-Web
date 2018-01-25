var path = require("path")
var webpack = require('webpack')
var BundleTracker = require('webpack-bundle-tracker')
var config = require('./webpack.base.config.js')

var ip = 'localhost';
var port = '8001';

config.entry = {
    DataEntry: ['./js/data-entry', 'webpack/hot/only-dev-server'],
    StudyArea: ['./js/study-area', 'webpack/hot/only-dev-server'],
    StatusQuo: ['./js/status-quo', 'webpack/hot/only-dev-server'],
    Base:      ['./js/base', 'webpack/hot/only-dev-server'],
    devServerClient: 'webpack-dev-server/client?http://0.0.0.0:' + port
}

config.output.path = path.resolve('./repair/static/bundles/dev/');
config.output.publicPath = 'http://' + ip + ':' + port + '/static/bundles/dev/';

config.devtool = "#eval-source-map";

config.plugins = config.plugins.concat([
  new webpack.HotModuleReplacementPlugin(),
  new webpack.NoEmitOnErrorsPlugin(),
  new BundleTracker({filename: './repair/webpack-stats-dev.json'}),
])
  
module.exports = config;