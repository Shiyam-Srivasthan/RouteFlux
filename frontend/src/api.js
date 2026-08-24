// Thin API client for the RouteFlux FastAPI backend.
// Contracts confirmed against backend/app/api/schemas.py and routes.py:
//   POST /graph/generate  { rows, cols, seed }                          -> GraphOut { nodes, roads }
//   GET  /graph                                                         -> GraphOut
//   POST /route            { source, destination, algorithm }           -> RouteResponse
//   POST /traffic/update   { source, destination, multiplier, bidirectional } -> GraphOut
//   POST /road/close       { source, destination, bidirectional }       -> GraphOut
//   POST /road/open        { source, destination, bidirectional }       -> GraphOut

const BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

export class ApiError extends Error {
  constructor(message, status, detail) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

function formatDetail(detail) {
  if (!detail) return null
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    // FastAPI/Pydantic validation error array: [{ loc, msg, type }, ...]
    return detail
      .map((d) => {
        const field = Array.isArray(d.loc) ? d.loc.slice(1).join('.') : 'value'
        return `${field}: ${d.msg}`
      })
      .join('; ')
  }
  return null
}

async function request(path, options = {}) {
  let response
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    })
  } catch (networkError) {
    throw new ApiError(`Cannot reach backend at ${BASE_URL}. Is the server running?`, 0, null)
  }

  if (!response.ok) {
    let body = null
    try {
      body = await response.json()
    } catch {
      // response had no JSON body
    }
    const detail = formatDetail(body?.detail)
    throw new ApiError(detail || `Request failed (HTTP ${response.status})`, response.status, body?.detail)
  }

  return response.json()
}

export const api = {
  generateGraph: (rows, cols, seed) =>
    request('/graph/generate', { method: 'POST', body: JSON.stringify({ rows, cols, seed }) }),

  getGraph: () => request('/graph'),

  computeRoute: (source, destination, algorithm) =>
    request('/route', {
      method: 'POST',
      body: JSON.stringify({ source, destination, algorithm }),
    }),

  updateTraffic: (source, destination, multiplier, bidirectional = false) =>
    request('/traffic/update', {
      method: 'POST',
      body: JSON.stringify({ source, destination, multiplier, bidirectional }),
    }),

  closeRoad: (source, destination, bidirectional = false) =>
    request('/road/close', {
      method: 'POST',
      body: JSON.stringify({ source, destination, bidirectional }),
    }),

  openRoad: (source, destination, bidirectional = false) =>
    request('/road/open', {
      method: 'POST',
      body: JSON.stringify({ source, destination, bidirectional }),
    }),
}
