(function () {
  const savedTheme = localStorage.getItem('blend_theme');
  if (savedTheme && savedTheme !== 'system') {
    document.documentElement.setAttribute('data-theme', savedTheme);
  }
  if (savedTheme === 'system') {
    const systemDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    document.documentElement.setAttribute('data-theme', systemDark ? 'dark' : 'light');
  }

  let defaultBackend = '';
  if (window.location.protocol === 'file:') {
    defaultBackend = 'http://127.0.0.1:5000';
  } else if ((window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') && window.location.port !== '5000') {
    // Allows UI development on a different port (like Live Server 5500) to still connect to the Python backend
    defaultBackend = 'http://127.0.0.1:5000';
  }
  const savedBackend = localStorage.getItem('blend_backend_url');

  window.BLEND_CONFIG = window.BLEND_CONFIG || {};
  window.BLEND_CONFIG.BACKEND_URL = (savedBackend || window.BLEND_CONFIG.BACKEND_URL || defaultBackend).replace(/\/$/, '');

  window.API = function API(path) {
    const normalizedPath = path.startsWith('/') ? path : '/' + path;
    return `${window.BLEND_CONFIG.BACKEND_URL}${normalizedPath}`;
  };

  const originalFetch = window.fetch;
  window.fetch = async function(...args) {
    let [resource, config] = args;
    if (typeof resource === 'string' && resource.includes('/api/')) {
      config = config || {};
      config.headers = config.headers || {};
      if (localStorage.getItem('blend_tor') === '1') {
        config.headers['X-Blend-Tor'] = '1';
      }
      if (localStorage.getItem('blend_proxy') === '1') {
        config.headers['X-Blend-Proxy'] = '1';
      }
    }
    return originalFetch(resource, config);
  };
})();
