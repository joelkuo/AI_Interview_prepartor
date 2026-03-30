const path = require("path");
const HtmlWebpackPlugin = require("html-webpack-plugin");
const CopyWebpackPlugin = require("copy-webpack-plugin");

module.exports = (env, argv) => {
  const isDev = argv.mode === "development";

  return {
    entry: "./src/taskpane/index.tsx",
    output: {
      path: path.resolve(__dirname, "dist"),
      filename: "taskpane.js",
      clean: true,
    },
    resolve: {
      extensions: [".ts", ".tsx", ".js"],
    },
    module: {
      rules: [
        {
          test: /\.tsx?$/,
          use: "ts-loader",
          exclude: /node_modules/,
        },
        {
          test: /\.css$/,
          use: ["style-loader", "css-loader"],
        },
      ],
    },
    plugins: [
      new HtmlWebpackPlugin({
        template: "./src/taskpane/index.html",
        filename: "taskpane.html",
      }),
      new CopyWebpackPlugin({
        patterns: [
          { from: "manifest.xml", to: "manifest.xml" },
          { from: "assets", to: "assets", noErrorOnMissing: true },
        ],
      }),
    ],
    devServer: {
      port: 3000,
      https: true,
      headers: {
        "Access-Control-Allow-Origin": "*",
      },
      static: {
        directory: path.join(__dirname, "dist"),
      },
    },
    mode: isDev ? "development" : "production",
    devtool: isDev ? "source-map" : false,
  };
};
