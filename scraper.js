const axios = require('axios');

const BASE_URL = 'https://icp.administracionelectronica.gob.es/icpplus';

// Headers to mimic real browser
const HEADERS = {
  'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
  'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
  'Accept-Language': 'es-ES,es;q=0.9',
  'Connection': 'keep-alive'
};

/**
 * Check if appointments are available for given province + tramite
 * Returns: { available: bool, oficinas: [], error: null|string }
 */
async function checkAppointments(provinciaCode, tramiteCode, oficinaCode = '') {
  try {
    const session = axios.create({
      baseURL: BASE_URL,
      headers: HEADERS,
      timeout: 30000,
      withCredentials: true
    });

    // Step 1: Load main page to get session/cookies
    const step1 = await session.get(`/index.html`);
    
    // Extract any hidden form fields if needed
    const cookies = step1.headers['set-cookie'] || [];
    const cookieStr = cookies.map(c => c.split(';')[0]).join('; ');

    // Step 2: Select province
    const step2 = await session.post(`/citar`, 
      new URLSearchParams({
        'pais': '000',
        'provincia': provinciaCode,
        'sede': '',
        'tramite': ''
      }).toString(),
      {
        headers: {
          ...HEADERS,
          'Content-Type': 'application/x-www-form-urlencoded',
          'Cookie': cookieStr,
          'Referer': `${BASE_URL}/index.html`
        }
      }
    );

    // Step 3: Select tramite
    const step3 = await session.post(`/acInfo`,
      new URLSearchParams({
        'provincia': provinciaCode,
        'tramite': tramiteCode,
        'sede': '',
        'btnAceptar': 'Aceptar'
      }).toString(),
      {
        headers: {
          ...HEADERS,
          'Content-Type': 'application/x-www-form-urlencoded',
          'Cookie': cookieStr,
          'Referer': `${BASE_URL}/citar`
        }
      }
    );

    // Step 4: Accept info page
    const step4 = await session.post(`/acEntrada`,
      new URLSearchParams({
        'btnEntrar': 'Entrar'
      }).toString(),
      {
        headers: {
          ...HEADERS,
          'Content-Type': 'application/x-www-form-urlencoded',
          'Cookie': cookieStr,
          'Referer': `${BASE_URL}/acInfo`
        }
      }
    );

    const html4 = step4.data;

    // Check if oficinas/appointments are available
    // If the page shows "En este momento no hay citas disponibles" → no slots
    if (html4.includes('En este momento no hay citas disponibles') ||
        html4.includes('no hay citas') ||
        html4.includes('no existen citas')) {
      return { available: false, oficinas: [], error: null };
    }

    // If page has oficina selection or appointment slots → available!
    if (html4.includes('oficina') || 
        html4.includes('COMISARIA') || 
        html4.includes('JEFATURA') ||
        html4.includes('btnSiguiente') ||
        html4.includes('Siguiente')) {
      
      // Extract oficina names from HTML
      const oficinas = extractOficinas(html4);
      return { available: true, oficinas, error: null };
    }

    // Blocked or error page
    if (html4.includes('Access Denied') || html4.includes('blocked')) {
      return { available: false, oficinas: [], error: 'BLOCKED' };
    }

    return { available: false, oficinas: [], error: null };

  } catch (err) {
    console.error(`Scraper error [${provinciaCode}/${tramiteCode}]:`, err.message);
    return { available: false, oficinas: [], error: err.message };
  }
}

/**
 * Extract oficina names from HTML response
 */
function extractOficinas(html) {
  const oficinas = [];
  
  // Match option values in select dropdowns
  const optionRegex = /<option[^>]*value="([^"]*)"[^>]*>([^<]+)<\/option>/gi;
  let match;
  while ((match = optionRegex.exec(html)) !== null) {
    const text = match[2].trim();
    if (text && text.length > 5 && !text.includes('Selecciona') && !text.includes('--')) {
      oficinas.push(text);
    }
  }

  // Also match button text (inline oficinas)
  const btnRegex = /value="(CNP[^"]+|JEFATURA[^"]+|COMISARIA[^"]+)"/gi;
  while ((match = btnRegex.exec(html)) !== null) {
    const text = match[1].trim();
    if (!oficinas.includes(text)) oficinas.push(text);
  }

  return oficinas;
}

/**
 * Fetch available tramites for a province dynamically
 */
async function fetchTramites(provinciaCode) {
  try {
    const session = axios.create({
      baseURL: BASE_URL,
      headers: HEADERS,
      timeout: 20000
    });

    const res = await session.post(`/citar`,
      new URLSearchParams({
        'pais': '000',
        'provincia': provinciaCode,
        'sede': '',
        'tramite': ''
      }).toString(),
      {
        headers: {
          ...HEADERS,
          'Content-Type': 'application/x-www-form-urlencoded',
          'Referer': `${BASE_URL}/index.html`
        }
      }
    );

    const html = res.data;
    const tramites = [];
    const optionRegex = /<option[^>]*value="([^"]*)"[^>]*>([^<]+)<\/option>/gi;
    let match;
    while ((match = optionRegex.exec(html)) !== null) {
      const code = match[1].trim();
      const name = match[2].trim();
      if (code && name && code !== '' && !name.includes('Selecciona')) {
        tramites.push({ code, name });
      }
    }
    return tramites;
  } catch (err) {
    console.error('fetchTramites error:', err.message);
    return [];
  }
}

module.exports = { checkAppointments, fetchTramites };
