var webpack = require('webpack')
var WebpackDevServer = require('webpack-dev-server')
var config = require('./repair/webpack.dev.config')

var ip = '0.0.0.0';
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
