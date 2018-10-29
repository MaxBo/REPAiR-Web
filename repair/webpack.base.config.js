var path = require('path');
var webpack = require('webpack');
var BundleTracker = require('webpack-bundle-tracker');
var ExtractTextPlugin = require("extract-text-webpack-plugin");

var entryPoints = {
    DataEntry: './js/data-entry',
    StudyArea: './js/study-area',
    StatusQuo: './js/status-quo',
    Targets:   './js/targets',
    Strategy:  './js/strategy',
    Welcome:   './js/welcome',
    Base:      './js/base',
};

module.exports = {
    context: __dirname,

    entry: entryPoints,

    output: {
        path: path.resolve('./repair/static/bundles/local/'),
        publicPath: '/static/bundles/local/',
        filename: '[name]-[hash].js'
    },

    plugins: [
        new webpack.optimize.CommonsChunkPlugin({
            name: 'commons',
            minChunks: function (module, count) {
                // workaround: webpack has problems bundling css files shared between entry points,
                // it is always missing  at one entry point then (which one seems random)
                // -> bundle all required css files into commons.css
                if(module.resource && (/^.*\.(css|scss)$/).test(module.resource)) {
                    return true;
                }
                // bundle node modules that are shared at least in between two different entry points
                return module.context && module.context.includes('node_modules') && count === 2;
            }
        }),
        new ExtractTextPlugin('[name]-[hash].css', {
            allChunks: true
        }),
        new webpack.ProvidePlugin({
            _: 'loadash',
            d3: 'd3',
            $: "jquery",
            jQuery: "jquery"
        }),
        new webpack.IgnorePlugin(/^codemirror$/)
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
                //use: ["style-loader", "css-loader"]
            },
            {
                test: /\.(png|woff|woff2|eot|ttf|svg|gif)$/,
                loader: 'url-loader?limit=100000'
            },
            {
                test: /\.less$/,
                use: ExtractTextPlugin.extract({
                    fallback: 'style-loader',
                    use: ['css-loader', 'less-loader']
                })
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
        }
    },
}

