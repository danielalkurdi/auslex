module.exports = {
	webpack: {
		configure: (config) => {
			if (config && Array.isArray(config.plugins)) {
				config.plugins = config.plugins.filter((p) => {
					const name = p && p.constructor && p.constructor.name;
					return name !== 'ForkTsCheckerWebpackPlugin';
				});
			}
			return config;
		}
	}
};
