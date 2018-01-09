var webpack = require('webpack')
var WebpackDevServer = require('webpack-dev-server')
var config = require('./webpack.dev.config')

var ip = 'localhost';
var port = '8001';

new WebpackDevServer(webpack(config), {
  publicPath: config.output.publicPath,
  hot: true,
  inline: true,
  historyApiFallback: true,
}).listen(port, ip, function (err, result) {
  if (err) {
    console.log(err)
  }

  console.log('Listening at ' + ip + ':' + port)
})