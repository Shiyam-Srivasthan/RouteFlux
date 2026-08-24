// Mirrors CONGESTION_LEVELS in backend/app/models.py. The API only accepts a
// raw multiplier (see PROJECT_CONTEXT.md), so the level->multiplier mapping
// is reproduced here for the traffic-simulation dropdown.
export const CONGESTION_LEVELS = {
  normal: 1.0,
  light: 1.2,
  moderate: 1.5,
  heavy: 2.0,
  severe: 3.0,
}

export function congestionColor(multiplier) {
  if (multiplier <= 1.0) return '#94a3b8' // slate - free flow
  if (multiplier <= 1.2) return '#facc15' // yellow - light
  if (multiplier <= 1.5) return '#fb923c' // orange - moderate
  if (multiplier <= 2.0) return '#f87171' // red - heavy
  return '#b91c1c' // dark red - severe
}
