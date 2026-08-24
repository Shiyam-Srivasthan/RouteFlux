export default function ControlPanel({
  rows,
  cols,
  seed,
  onRowsChange,
  onColsChange,
  onSeedChange,
  onGenerate,
  generating,
  nodes,
  source,
  destination,
  onSourceChange,
  onDestinationChange,
  algorithm,
  onAlgorithmChange,
  onFindRoute,
  routing,
}) {
  const canFindRoute = nodes.length > 0 && source !== '' && destination !== '' && !routing

  return (
    <section className="panel">
      <h2>Graph</h2>
      <div className="field-row">
        <label>
          Rows
          <input type="number" min={1} max={100} value={rows} onChange={(e) => onRowsChange(Number(e.target.value))} />
        </label>
        <label>
          Cols
          <input type="number" min={1} max={100} value={cols} onChange={(e) => onColsChange(Number(e.target.value))} />
        </label>
        <label>
          Seed
          <input type="number" value={seed} onChange={(e) => onSeedChange(Number(e.target.value))} />
        </label>
      </div>
      <button className="btn btn-primary" onClick={onGenerate} disabled={generating}>
        {generating ? 'Generating…' : 'Generate Graph'}
      </button>

      <h2>Route</h2>
      <div className="field-row">
        <label>
          Source
          <select value={source} onChange={(e) => onSourceChange(e.target.value)} disabled={nodes.length === 0}>
            <option value="">Select…</option>
            {nodes.map((n) => (
              <option key={n.id} value={n.id}>
                {n.id}
              </option>
            ))}
          </select>
        </label>
        <label>
          Destination
          <select value={destination} onChange={(e) => onDestinationChange(e.target.value)} disabled={nodes.length === 0}>
            <option value="">Select…</option>
            {nodes.map((n) => (
              <option key={n.id} value={n.id}>
                {n.id}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div className="field-row">
        <label className="algorithm-select">
          Algorithm
          <select value={algorithm} onChange={(e) => onAlgorithmChange(e.target.value)}>
            <option value="dijkstra">Dijkstra</option>
            <option value="astar">A*</option>
          </select>
        </label>
      </div>
      <button className="btn btn-primary" onClick={onFindRoute} disabled={!canFindRoute}>
        {routing ? 'Computing…' : 'Find Route'}
      </button>
    </section>
  )
}
