var path = require("path")
var webpack = require('webpack')
var BundleTracker = require('webpack-bundle-tracker')
var config = require('./webpack.base.config.js')
const Uglify = require("uglifyjs-webpack-plugin");

config.output.path = path.resolve('./repair/static/bundles/prod/');
config.output.publicPath = '/static/bundles/prod/';

config.plugins = config.plugins.concat([
  new BundleTracker({filename: './webpack-stats-prod.json'}),

  // minifies the code
  new Uglify({
    compressor: {
      warnings: false
    }
  })
])

module.exports = config;