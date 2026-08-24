export default function MetricsPanel({ routeResult }) {
  if (!routeResult) {
    return (
      <section className="panel">
        <h2>Route Metrics</h2>
        <p className="muted">No route computed yet.</p>
      </section>
    )
  }

  if (!routeResult.reachable) {
    return (
      <section className="panel">
        <h2>Route Metrics</h2>
        <p className="metric-error">No route found — destination is unreachable from the source with the current graph state.</p>
        <dl className="metrics">
          <dt>Algorithm</dt>
          <dd>{routeResult.algorithm}</dd>
          <dt>Nodes explored</dt>
          <dd>{routeResult.nodes_explored}</dd>
          <dt>Runtime</dt>
          <dd>{routeResult.runtime_ms.toFixed(3)} ms</dd>
        </dl>
      </section>
    )
  }

  return (
    <section className="panel">
      <h2>Route Metrics</h2>
      <dl className="metrics">
        <dt>Algorithm</dt>
        <dd>{routeResult.algorithm}</dd>
        <dt>Reachable</dt>
        <dd>Yes</dd>
        <dt>Cost (travel time, h)</dt>
        <dd>{routeResult.cost.toFixed(4)}</dd>
        <dt>Nodes explored</dt>
        <dd>{routeResult.nodes_explored}</dd>
        <dt>Runtime</dt>
        <dd>{routeResult.runtime_ms.toFixed(3)} ms</dd>
        <dt>Nodes in path</dt>
        <dd>{routeResult.path.length}</dd>
      </dl>
    </section>
  )
}
