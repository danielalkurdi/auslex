const path = require('path');
const webpack = require('webpack');

module.exports = {
  // Enable webpack optimizations
  optimization: {
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all',
          priority: 10,
          enforce: true
        },
        react: {
          test: /[\\/]node_modules[\\/](react|react-dom)[\\/]/,
          name: 'react',
          chunks: 'all',
          priority: 20,
          enforce: true
        },
        common: {
          name: 'common',
          minChunks: 2,
          chunks: 'all',
          priority: 5,
          reuseExistingChunk: true
        }
      }
    },
    usedExports: true,
    sideEffects: false,
    runtimeChunk: 'single',
    minimize: process.env.NODE_ENV === 'production'
  },
  
  // Performance budgets and hints
  performance: {
    maxAssetSize: 250000,
    maxEntrypointSize: 250000,
    hints: process.env.NODE_ENV === 'production' ? 'warning' : false
  },
  
  // Bundle analyzer for production builds
  ...(process.env.ANALYZE && {
    plugins: [
      new (require('webpack-bundle-analyzer').BundleAnalyzerPlugin)({
        analyzerMode: 'server',
        openAnalyzer: true
      })
    ]
  }),
  
  resolve: {
    // Optimize module resolution
    alias: {
      '@': path.resolve(__dirname, 'src'),
      '@components': path.resolve(__dirname, 'src/components'),
      '@utils': path.resolve(__dirname, 'src/utils'),
      '@services': path.resolve(__dirname, 'src/services')
    },
    extensions: ['.js', '.jsx', '.ts', '.tsx', '.json'],
    modules: ['node_modules', path.resolve(__dirname, 'src')]
  },
  
  module: {
    rules: [
      {
        test: /\.(js|jsx|ts|tsx)$/,
        exclude: /node_modules/,
        use: [
          {
            loader: 'babel-loader',
            options: {
              presets: [
                ['@babel/preset-env', {
                  targets: {
                    browsers: ['>0.2%', 'not dead', 'not op_mini all']
                  },
                  modules: false,
                  useBuiltIns: 'usage',
                  corejs: 3
                }],
                '@babel/preset-react'
              ],
              plugins: [
                '@babel/plugin-syntax-dynamic-import',
                '@babel/plugin-proposal-class-properties',
                // Enable React optimization
                process.env.NODE_ENV === 'production' && [
                  'babel-plugin-transform-react-remove-prop-types',
                  { removeImport: true }
                ]
              ].filter(Boolean),
              cacheDirectory: true
            }
          }
        ]
      },
      {
        test: /\.(png|jpe?g|gif|svg|ico)$/i,
        type: 'asset',
        parser: {
          dataUrlCondition: {
            maxSize: 8 * 1024 // 8kb
          }
        },
        generator: {
          filename: 'static/media/[name].[contenthash:8][ext]'
        }
      },
      {
        test: /\.(woff|woff2|eot|ttf|otf)$/i,
        type: 'asset/resource',
        generator: {
          filename: 'static/fonts/[name].[contenthash:8][ext]'
        }
      }
    ]
  },

  // Development optimizations
  ...(process.env.NODE_ENV === 'development' && {
    devtool: 'eval-source-map',
    cache: {
      type: 'filesystem',
      buildDependencies: {
        config: [__filename]
      }
    }
  }),

  // Production optimizations
  ...(process.env.NODE_ENV === 'production' && {
    devtool: false,
    plugins: [
      new webpack.DefinePlugin({
        'process.env.NODE_ENV': JSON.stringify('production')
      }),
      // Tree shaking for unused code
      new webpack.optimize.ModuleConcatenationPlugin()
    ]
  })
};