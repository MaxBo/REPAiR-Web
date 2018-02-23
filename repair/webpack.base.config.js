var path = require('path');
var webpack = require('webpack');
var BundleTracker = require('webpack-bundle-tracker');

module.exports = {
  context: __dirname,
  entry: {
    DataEntry: './js/data-entry',
    StudyArea: './js/study-area',
    StatusQuo: './js/status-quo',
    Base:      './js/base',
  },
  
  output: {
    path: path.resolve('./repair/static/bundles/local/'),
    publicPath: '/static/bundles/local/',
    filename: "[name]-[hash].js"
  },

  plugins: [
    // deactivated because karma doesn't understand the chunks
    //new webpack.optimize.CommonsChunkPlugin({ name: 'vendors', filename: 'vendors.js' }),
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
        test: /\.js$/,
         exclude: /(node_modules|bower_components)/,
         use: {
           loader: 'babel-loader',
           options: {
             presets: ['babel-preset-env']
           }
        }
      },
      {
        test: /\.css$/,
        use: [
          { loader: 'style-loader' },
          {
            loader: 'css-loader',
            options: {
              modules: true
            }
          }
        ]
      }
    ],
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

