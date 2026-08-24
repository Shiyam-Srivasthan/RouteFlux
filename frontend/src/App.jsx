import { useCallback, useEffect, useState } from 'react'
import { api, ApiError } from './api.js'
import { CONGESTION_LEVELS } from './congestion.js'
import ControlPanel from './components/ControlPanel.jsx'
import GraphVisualizer from './components/GraphVisualizer.jsx'
import MetricsPanel from './components/MetricsPanel.jsx'
import TrafficControls from './components/TrafficControls.jsx'

const DEFAULT_ROWS = 10
const DEFAULT_COLS = 10
const DEFAULT_SEED = 42

export default function App() {
  const [rows, setRows] = useState(DEFAULT_ROWS)
  const [cols, setCols] = useState(DEFAULT_COLS)
  const [seed, setSeed] = useState(DEFAULT_SEED)

  const [graph, setGraph] = useState(null)
  const [source, setSource] = useState('')
  const [destination, setDestination] = useState('')
  const [algorithm, setAlgorithm] = useState('dijkstra')
  const [routeResult, setRouteResult] = useState(null)

  const [selectedRoad, setSelectedRoad] = useState(null)
  const [congestionLevel, setCongestionLevel] = useState('heavy')
  const [bidirectional, setBidirectional] = useState(false)

  const [pending, setPending] = useState(null) // null | 'generate' | 'route' | 'traffic'
  const [error, setError] = useState(null)

  const handleGenerate = useCallback(async (r = rows, c = cols, s = seed) => {
    setPending('generate')
    setError(null)
    try {
      const data = await api.generateGraph(r, c, s)
      setGraph(data)
      setRouteResult(null)
      setSource('')
      setDestination('')
      setSelectedRoad(null)
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Failed to generate graph.')
    } finally {
      setPending(null)
    }
  }, [rows, cols, seed])

  // auto-generate a default graph on first load so the demo works immediately
  useEffect(() => {
    handleGenerate(DEFAULT_ROWS, DEFAULT_COLS, DEFAULT_SEED)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const findRoute = useCallback(
    async (src = source, dst = destination, algo = algorithm) => {
      if (src === '' || dst === '') return
      setPending('route')
      setError(null)
      try {
        const result = await api.computeRoute(Number(src), Number(dst), algo)
        setRouteResult(result)
      } catch (e) {
        setError(e instanceof ApiError ? e.message : 'Failed to compute route.')
      } finally {
        setPending(null)
      }
    },
    [source, destination, algorithm],
  )

  const handleFindRoute = () => findRoute()

  // After any graph mutation (traffic/closure), if a route was already
  // computed, recompute it so the change — and any rerouting — is visible
  // immediately without an extra click.
  const rerouteIfActive = useCallback(async () => {
    if (source !== '' && destination !== '' && routeResult) {
      await findRoute()
    }
  }, [source, destination, routeResult, findRoute])

  const handleApplyTraffic = useCallback(async () => {
    if (!selectedRoad) return
    setPending('traffic')
    setError(null)
    try {
      const multiplier = CONGESTION_LEVELS[congestionLevel]
      const data = await api.updateTraffic(selectedRoad.source, selectedRoad.destination, multiplier, bidirectional)
      setGraph(data)
      await rerouteIfActive()
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Failed to update traffic.')
    } finally {
      setPending(null)
    }
  }, [selectedRoad, congestionLevel, bidirectional, rerouteIfActive])

  const handleCloseRoad = useCallback(async () => {
    if (!selectedRoad) return
    setPending('traffic')
    setError(null)
    try {
      const data = await api.closeRoad(selectedRoad.source, selectedRoad.destination, bidirectional)
      setGraph(data)
      await rerouteIfActive()
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Failed to close road.')
    } finally {
      setPending(null)
    }
  }, [selectedRoad, bidirectional, rerouteIfActive])

  const handleOpenRoad = useCallback(async () => {
    if (!selectedRoad) return
    setPending('traffic')
    setError(null)
    try {
      const data = await api.openRoad(selectedRoad.source, selectedRoad.destination, bidirectional)
      setGraph(data)
      await rerouteIfActive()
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Failed to reopen road.')
    } finally {
      setPending(null)
    }
  }, [selectedRoad, bidirectional, rerouteIfActive])

  const nodes = graph?.nodes ?? []
  const roads = graph?.roads ?? []

  return (
    <div className="app">
      <header className="app-header">
        <h1>RouteFlux</h1>
        <p>Dynamic traffic routing &amp; rerouting engine — Dijkstra vs A* demo</p>
      </header>

      {error && (
        <div className="error-banner" role="alert">
          {error}
          <button className="error-dismiss" onClick={() => setError(null)} aria-label="Dismiss error">
            ×
          </button>
        </div>
      )}

      <div className="layout">
        <aside className="sidebar">
          <ControlPanel
            rows={rows}
            cols={cols}
            seed={seed}
            onRowsChange={setRows}
            onColsChange={setCols}
            onSeedChange={setSeed}
            onGenerate={() => handleGenerate()}
            generating={pending === 'generate'}
            nodes={nodes}
            source={source}
            destination={destination}
            onSourceChange={setSource}
            onDestinationChange={setDestination}
            algorithm={algorithm}
            onAlgorithmChange={setAlgorithm}
            onFindRoute={handleFindRoute}
            routing={pending === 'route'}
          />

          <TrafficControls
            roads={roads}
            selectedRoad={selectedRoad}
            onSelectRoad={setSelectedRoad}
            level={congestionLevel}
            onLevelChange={setCongestionLevel}
            onApplyTraffic={handleApplyTraffic}
            onCloseRoad={handleCloseRoad}
            onOpenRoad={handleOpenRoad}
            bidirectional={bidirectional}
            onBidirectionalChange={setBidirectional}
            busy={pending === 'traffic'}
          />

          <MetricsPanel routeResult={routeResult} />
        </aside>

        <main className="main-area">
          <GraphVisualizer
            graph={graph}
            source={source}
            destination={destination}
            routePath={routeResult?.reachable ? routeResult.path : null}
            selectedRoad={selectedRoad}
            onSelectRoad={setSelectedRoad}
          />
        </main>
      </div>
    </div>
  )
}
