import { CONGESTION_LEVELS } from '../congestion.js'

function roadLabel(road) {
  const status = road.is_open ? `x${road.congestion_multiplier.toFixed(1)}` : 'closed'
  return `${road.source} → ${road.destination}  (${status})`
}

function roadKey(road) {
  return `${road.source}-${road.destination}`
}

export default function TrafficControls({
  roads,
  selectedRoad,
  onSelectRoad,
  level,
  onLevelChange,
  onApplyTraffic,
  onCloseRoad,
  onOpenRoad,
  bidirectional,
  onBidirectionalChange,
  busy,
}) {
  const hasSelection = Boolean(selectedRoad)
  const selectedValue = selectedRoad ? roadKey(selectedRoad) : ''

  const handleSelect = (e) => {
    const value = e.target.value
    if (!value) {
      onSelectRoad(null)
      return
    }
    const [source, destination] = value.split('-').map(Number)
    onSelectRoad({ source, destination })
  }

  return (
    <section className="panel">
      <h2>Traffic &amp; Closures</h2>
      <label>
        Road
        <select value={selectedValue} onChange={handleSelect} disabled={roads.length === 0}>
          <option value="">Select a road…</option>
          {roads.map((road) => (
            <option key={roadKey(road)} value={roadKey(road)}>
              {roadLabel(road)}
            </option>
          ))}
        </select>
      </label>

      <label className="checkbox-row">
        <input type="checkbox" checked={bidirectional} onChange={(e) => onBidirectionalChange(e.target.checked)} />
        Apply to both directions
      </label>

      <label>
        Congestion level
        <select value={level} onChange={(e) => onLevelChange(e.target.value)}>
          {Object.entries(CONGESTION_LEVELS).map(([name, multiplier]) => (
            <option key={name} value={name}>
              {name} (x{multiplier})
            </option>
          ))}
        </select>
      </label>
      <button className="btn" onClick={onApplyTraffic} disabled={!hasSelection || busy}>
        Apply Traffic
      </button>

      <div className="field-row">
        <button className="btn btn-danger" onClick={onCloseRoad} disabled={!hasSelection || busy}>
          Close Road
        </button>
        <button className="btn btn-success" onClick={onOpenRoad} disabled={!hasSelection || busy}>
          Reopen Road
        </button>
      </div>
    </section>
  )
}
