import { congestionColor } from '../congestion.js'

const WIDTH = 800
const HEIGHT = 800
const PADDING = 36

// Layout is derived entirely from node.x/node.y returned by the backend —
// nothing here is hard-coded to a particular grid size.
function computeLayout(nodes) {
  const xs = nodes.map((n) => n.x)
  const ys = nodes.map((n) => n.y)
  const minX = Math.min(...xs)
  const maxX = Math.max(...xs)
  const minY = Math.min(...ys)
  const maxY = Math.max(...ys)
  const rangeX = maxX - minX || 1
  const rangeY = maxY - minY || 1
  const scale = Math.min((WIDTH - 2 * PADDING) / rangeX, (HEIGHT - 2 * PADDING) / rangeY)

  const project = (x, y) => [PADDING + (x - minX) * scale, PADDING + (y - minY) * scale]

  // approximate grid dimensions from distinct coordinate values, purely to
  // size nodes/labels sensibly — never used to position anything
  const cols = new Set(xs).size
  const rows = new Set(ys).size
  const spacingPx = Math.min(WIDTH, HEIGHT) / Math.max(cols, rows, 1)
  const radius = Math.max(3, Math.min(11, spacingPx * 0.28))

  return { project, radius }
}

function offsetForDirection(x1, y1, x2, y2, hasReverse, isForwardOrder) {
  if (!hasReverse) return [0, 0]
  const dx = x2 - x1
  const dy = y2 - y1
  const len = Math.hypot(dx, dy) || 1
  const nx = -dy / len
  const ny = dx / len
  const sign = isForwardOrder ? 1 : -1
  const offset = 2.5
  return [nx * offset * sign, ny * offset * sign]
}

export default function GraphVisualizer({ graph, source, destination, routePath, selectedRoad, onSelectRoad }) {
  if (!graph || graph.nodes.length === 0) {
    return (
      <div className="graph-visualizer graph-visualizer--empty">
        <p>No graph loaded. Generate one to get started.</p>
      </div>
    )
  }

  const { project, radius } = computeLayout(graph.nodes)
  const nodePositions = new Map(graph.nodes.map((n) => [n.id, project(n.x, n.y)]))

  const roadPairKey = (a, b) => `${Math.min(a, b)}-${Math.max(a, b)}`
  const reverseExists = new Set()
  const seenPairs = new Set()
  for (const road of graph.roads) {
    const key = roadPairKey(road.source, road.destination)
    if (seenPairs.has(key)) reverseExists.add(key)
    seenPairs.add(key)
  }

  const routeEdgeKeys = new Set()
  if (routePath && routePath.length > 1) {
    for (let i = 0; i < routePath.length - 1; i++) {
      routeEdgeKeys.add(`${routePath[i]}->${routePath[i + 1]}`)
    }
  }
  const routeNodeSet = new Set(routePath || [])

  const roadLines = graph.roads.map((road) => {
    const from = nodePositions.get(road.source)
    const to = nodePositions.get(road.destination)
    if (!from || !to) return null

    const key = roadPairKey(road.source, road.destination)
    const hasReverse = reverseExists.has(key)
    const [ox, oy] = offsetForDirection(from[0], from[1], to[0], to[1], hasReverse, road.source < road.destination)

    const isOnRoute = routeEdgeKeys.has(`${road.source}->${road.destination}`)
    const isSelected = selectedRoad && selectedRoad.source === road.source && selectedRoad.destination === road.destination

    let stroke = congestionColor(road.congestion_multiplier)
    let strokeWidth = 2.5
    let dashArray = undefined
    let opacity = 0.85

    if (!road.is_open) {
      stroke = '#cbd5e1'
      dashArray = '6 4'
      opacity = 0.7
    }
    if (isOnRoute && road.is_open) {
      stroke = '#2563eb'
      strokeWidth = 5
      opacity = 1
    }

    return (
      <g key={`${road.source}-${road.destination}`}>
        <line
          x1={from[0] + ox}
          y1={from[1] + oy}
          x2={to[0] + ox}
          y2={to[1] + oy}
          stroke={stroke}
          strokeWidth={strokeWidth}
          strokeDasharray={dashArray}
          strokeLinecap="round"
          opacity={opacity}
          className="road-line"
          onClick={() => onSelectRoad && onSelectRoad({ source: road.source, destination: road.destination })}
        />
        {isSelected && (
          <line
            x1={from[0] + ox}
            y1={from[1] + oy}
            x2={to[0] + ox}
            y2={to[1] + oy}
            stroke="#9333ea"
            strokeWidth={strokeWidth + 4}
            strokeLinecap="round"
            opacity={0.35}
            pointerEvents="none"
          />
        )}
      </g>
    )
  })

  const nodeCircles = graph.nodes.map((node) => {
    const [x, y] = project(node.x, node.y)
    const isSource = source !== '' && Number(source) === node.id
    const isDestination = destination !== '' && Number(destination) === node.id
    const isOnRoute = routeNodeSet.has(node.id)

    let fill = '#64748b'
    let r = radius
    if (isOnRoute) {
      fill = '#93c5fd'
    }
    if (isSource) {
      fill = '#16a34a'
      r = radius * 1.3
    }
    if (isDestination) {
      fill = '#dc2626'
      r = radius * 1.3
    }

    return (
      <g key={node.id}>
        <circle cx={x} cy={y} r={r} fill={fill} stroke="#1e293b" strokeWidth={1} />
        {radius >= 5 && (
          <text x={x} y={y - r - 3} textAnchor="middle" fontSize={9} fill="#334155" className="node-label">
            {node.id}
          </text>
        )}
      </g>
    )
  })

  return (
    <div className="graph-visualizer">
      <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="graph-svg" role="img" aria-label="Road network visualization">
        <g>{roadLines}</g>
        <g>{nodeCircles}</g>
      </svg>
      <div className="legend">
        <span className="legend-item"><span className="swatch" style={{ background: '#16a34a' }} /> Source</span>
        <span className="legend-item"><span className="swatch" style={{ background: '#dc2626' }} /> Destination</span>
        <span className="legend-item"><span className="swatch" style={{ background: '#2563eb' }} /> Route</span>
        <span className="legend-item"><span className="swatch" style={{ background: '#fb923c' }} /> Congested</span>
        <span className="legend-item"><span className="swatch swatch--dashed" /> Closed</span>
        <span className="legend-item"><span className="swatch" style={{ background: '#9333ea', opacity: 0.5 }} /> Selected road</span>
      </div>
    </div>
  )
}
