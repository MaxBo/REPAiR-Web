var webpack = require('webpack')
var WebpackDevServer = require('webpack-dev-server')
var config = require('./repair/webpack.dev.config')

var ip = '0.0.0.0';
var port = '8001';

var options = {
  publicPath: config.output.publicPath,
  hot: true,
  inline: true,
  historyApiFallback: true,
  watchOptions: {
	  poll: 1000,
  }
}
new WebpackDevServer(webpack(config), options).listen(port, ip, function (err, result) {
  if (err) {
    console.log(err)
  }

  console.log('Listening at ' + ip + ':' + port)
})
