var path = require("path");
var webpack = require('webpack');
var BundleTracker = require('webpack-bundle-tracker');
var config = require('./webpack.base.config.js');
const Uglify = require("uglifyjs-webpack-plugin");

config.output.path = path.resolve('./repair/static/bundles/staged/');
config.output.publicPath = '/static/bundles/staged/';

config.devtool = "#eval-source-map";

config.plugins = config.plugins.concat([
  new BundleTracker({filename: './repair/webpack-stats-staged.json'}),
  // minify the code
  // WARNING: beta version is used here, because normal version (see below) does not support ES6

  new Uglify({
    compressor: {
      warnings: false
    }
  })
])
  
module.exports = config;