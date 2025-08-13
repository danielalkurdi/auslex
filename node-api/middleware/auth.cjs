function requireApiKey(req, res, next) {
  const required = process.env.AUSLEX_API_KEY;
  if (!required) return next();
  const got = req.header('x-auslex-key');
  if (got && got === required) return next();
  return res.status(401).json({ error: 'Unauthorized' });
}

module.exports = { requireApiKey };

