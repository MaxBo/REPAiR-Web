var path = require("path")
var webpack = require('webpack')
var BundleTracker = require('webpack-bundle-tracker')
var config = require('./webpack.base.config.js')
const Uglify = require("uglifyjs-webpack-plugin");

config.output.path = path.resolve('./repair/static/bundles/prod/');
config.output.publicPath = '/static/bundles/prod/';
// no hashes in production
config.output.filename = '[name].js';

config.plugins = config.plugins.concat([
  new BundleTracker({filename: path.resolve('./repair/webpack-stats-prod.json')}),

  // minify the code
  // WARNING: beta version is used here, because normal version (see below) does not support ES6

  new Uglify({
    compressor: {
      warnings: false
    }
  })
  //new webpack.optimize.UglifyJsPlugin({
    //compressor: {
      //warnings: false
    //}
  //})
])

module.exports = config;