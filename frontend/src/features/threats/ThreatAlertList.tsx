import React, { useEffect, useState } from 'react'
import {
  AlertTriangle,
  RefreshCw,
  Clock,
  Filter,
  ShieldAlert,
  ArrowRight,
  FileCode,
} from 'lucide-react'
import { Card } from '../../components/common/Card'
import { Badge } from '../../components/common/Badge'
import { Button } from '../../components/common/Button'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/common/ErrorBanner'
import { fetchDetections } from '../../api'
import { Detection } from '../../types'
import { NavTab } from '../../components/layout/Sidebar'

interface ThreatAlertListProps {
  initialJobId?: string
  initialAgentId?: string
  onNavigate?: (tab: NavTab, context?: { jobId?: string; agentId?: string }) => void
}

export const ThreatAlertList: React.FC<ThreatAlertListProps> = ({
  initialJobId,
  initialAgentId,
  onNavigate,
}) => {
  const [detections, setDetections] = useState<Detection[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [severityFilter, setSeverityFilter] = useState<string>('all')
  const [ruleFilter, setRuleFilter] = useState<string>('all')
  const [jobIdFilter, setJobIdFilter] = useState<string>(initialJobId || '')
  const [agentIdFilter, setAgentIdFilter] = useState<string>(initialAgentId || '')
  const [selectedDetection, setSelectedDetection] = useState<Detection | null>(null)
  const [showRawJson, setShowRawJson] = useState(false)

  const loadDetections = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const res = await fetchDetections({
        severity: severityFilter !== 'all' ? severityFilter : undefined,
        ruleId: ruleFilter !== 'all' ? ruleFilter : undefined,
        jobId: jobIdFilter || undefined,
        agentId: agentIdFilter || undefined,
        limit: 100,
      })
      setDetections(res.items || [])
    } catch (err: any) {
      setError(err.message || 'Unable to retrieve detections from detection service.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadDetections()
  }, [severityFilter, ruleFilter, jobIdFilter, agentIdFilter])

  const getSeverityBadge = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return <Badge variant="danger">CRITICAL</Badge>
      case 'high':
        return <Badge variant="danger">HIGH</Badge>
      case 'medium':
        return <Badge variant="warning">MEDIUM</Badge>
      case 'low':
        return <Badge variant="info">LOW</Badge>
      default:
        return <Badge variant="default">{severity.toUpperCase()}</Badge>
    }
  }

  const knownRules = [
    'all',
    'PROC-UNSIGNED-001',
    'PROC-NET-001',
    'PROC-PARENT-001',
    'AUTORUN-SUSP-001',
    'USER-SUSP-001',
    'FLAG-DYNAMIC-001',
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 tracking-tight">Threat Detections & Evidence Triage</h1>
          <p className="text-sm text-slate-400 mt-1">
            Explainable, deterministic detection matches correlated across ingested endpoint telemetry.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={loadDetections}>
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </Button>
        </div>
      </div>

      {error && <ErrorBanner message={error} onRetry={loadDetections} />}

      {/* Filter Toolbar */}
      <div className="space-y-3">
        {/* Severity Filter */}
        <div className="flex flex-wrap gap-2 items-center">
          <span className="text-xs text-slate-400 font-mono flex items-center gap-1.5 mr-1">
            <Filter className="w-3.5 h-3.5 text-rose-400" />
            Severity:
          </span>
          {['all', 'critical', 'high', 'medium', 'low'].map((sev) => (
            <button
              key={sev}
              onClick={() => setSeverityFilter(sev)}
              className={`px-2.5 py-1 text-xs rounded-md font-mono capitalize transition-colors ${
                severityFilter === sev
                  ? 'bg-rose-950 border border-rose-800 text-rose-300 font-bold'
                  : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              {sev}
            </button>
          ))}
        </div>

        {/* Rule Filter Bar */}
        <div className="flex flex-wrap gap-1.5 items-center">
          <span className="text-xs text-slate-400 font-mono mr-1">Rule ID:</span>
          {knownRules.map((r) => (
            <button
              key={r}
              onClick={() => setRuleFilter(r)}
              className={`px-2 py-0.5 text-[11px] rounded font-mono transition-colors ${
                ruleFilter === r
                  ? 'bg-cyan-950 border border-cyan-800 text-cyan-400 font-bold'
                  : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              {r}
            </button>
          ))}
        </div>
      </div>

      {/* Main Detections List */}
      {isLoading ? (
        <LoadingSpinner label="Evaluating adversary detection events..." />
      ) : detections.length === 0 ? (
        <EmptyState
          icon={<ShieldAlert className="w-6 h-6 text-slate-500" />}
          title="No threat detections recorded"
          description={
            severityFilter !== 'all' || ruleFilter !== 'all' || jobIdFilter
              ? 'No detections match your current filter selection.'
              : 'No suspicious artifacts or rule violations have triggered detections yet.'
          }
          actionLabel="Clear Filters"
          onAction={() => {
            setSeverityFilter('all')
            setRuleFilter('all')
            setJobIdFilter('')
            setAgentIdFilter('')
          }}
        />
      ) : (
        <div className="grid grid-cols-1 gap-3">
          {detections.map((det) => (
            <Card
              key={det.id}
              onClick={() => setSelectedDetection(det)}
              className="hover:border-rose-900/60 transition-all cursor-pointer bg-slate-900/40 p-4 border-slate-800/80"
            >
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                <div className="space-y-1.5 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    {getSeverityBadge(det.severity)}
                    <span className="px-2 py-0.5 rounded bg-slate-800 text-cyan-400 font-mono text-xs border border-slate-700">
                      {det.rule_id}
                    </span>
                    <span className="font-mono text-xs text-slate-400">{det.id}</span>
                  </div>

                  <h3 className="text-sm font-bold text-slate-100">{det.title}</h3>
                  <p className="text-xs text-slate-400 leading-relaxed max-w-3xl">
                    {det.description || 'Deterministic rule match observed in ingested forensic telemetry.'}
                  </p>

                  <div className="flex items-center gap-4 text-xs font-mono text-slate-400 pt-1">
                    <span>
                      Agent: <strong className="text-slate-200">{det.agent_id}</strong>
                    </span>
                    {det.job_id && (
                      <span>
                        Job: <strong className="text-cyan-400">{det.job_id}</strong>
                      </span>
                    )}
                    <span>
                      Supporting Evidence:{' '}
                      <strong className="text-emerald-400">{det.evidence.length} artifact(s)</strong>
                    </span>
                  </div>
                </div>

                <div className="text-right flex flex-col items-end justify-between self-stretch shrink-0">
                  <span className="text-[11px] text-slate-500 flex items-center gap-1 font-mono">
                    <Clock className="w-3 h-3" />
                    {new Date(det.created_at).toLocaleTimeString()}
                  </span>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation()
                      setSelectedDetection(det)
                    }}
                    className="mt-2 text-rose-300 border-rose-900/40 hover:bg-rose-950/40"
                  >
                    Triage Evidence
                    <ArrowRight className="w-3 h-3 ml-1" />
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Detailed Triage Modal */}
      {selectedDetection && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <Card className="w-full max-w-2xl max-h-[85vh] overflow-y-auto border-rose-800/60 bg-[#0d1322] shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2.5">
                <AlertTriangle className="w-5 h-5 text-rose-400" />
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-bold text-slate-100 font-mono">{selectedDetection.id}</h3>
                    {getSeverityBadge(selectedDetection.severity)}
                  </div>
                  <p className="text-xs text-cyan-400 font-mono mt-0.5">
                    Triggered by rule: {selectedDetection.rule_id}
                  </p>
                </div>
              </div>
              <Button variant="ghost" size="sm" onClick={() => setSelectedDetection(null)}>
                ✕ Close
              </Button>
            </div>

            {/* Explanation & Metadata */}
            <div className="space-y-3 font-mono text-xs">
              <div className="p-3 bg-slate-900/70 rounded-lg border border-slate-800 space-y-1">
                <h4 className="text-slate-200 font-bold text-xs">{selectedDetection.title}</h4>
                <p className="text-slate-400 text-[11px] leading-relaxed">
                  {selectedDetection.description}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="p-2.5 bg-slate-900/60 rounded-lg border border-slate-800">
                  <span className="text-slate-500 block text-[10px] uppercase">Associated Agent</span>
                  <span className="text-slate-200 font-medium">{selectedDetection.agent_id}</span>
                </div>
                <div className="p-2.5 bg-slate-900/60 rounded-lg border border-slate-800">
                  <span className="text-slate-500 block text-[10px] uppercase">Originating Job</span>
                  <span className="text-cyan-400 font-medium">{selectedDetection.job_id || 'N/A'}</span>
                </div>
              </div>

              {/* Supporting Evidence Chain */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                    Evidence Chain ({selectedDetection.evidence.length} artifact references)
                  </span>
                  <button
                    onClick={() => setShowRawJson(!showRawJson)}
                    className="text-[11px] text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
                  >
                    <FileCode className="w-3 h-3" />
                    <span>{showRawJson ? 'Structured View' : 'Raw JSON'}</span>
                  </button>
                </div>

                {showRawJson ? (
                  <pre className="text-[11px] text-slate-300 bg-slate-950 p-3 rounded overflow-x-auto border border-slate-800">
                    {JSON.stringify(selectedDetection, null, 2)}
                  </pre>
                ) : (
                  <div className="space-y-2">
                    {selectedDetection.evidence.map((ev, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 space-y-2"
                      >
                        <div className="flex items-center justify-between text-[11px]">
                          <div className="flex items-center gap-2">
                            <span className="px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800 font-semibold">
                              {ev.type}
                            </span>
                            <span className="text-slate-400 font-mono">{ev.artifact_id}</span>
                          </div>
                          {onNavigate && selectedDetection.job_id && (
                            <button
                              onClick={() => {
                                setSelectedDetection(null)
                                onNavigate('results', { jobId: selectedDetection.job_id })
                              }}
                              className="text-cyan-400 hover:text-cyan-300 text-[10px] underline"
                            >
                              Inspect in Artifacts →
                            </button>
                          )}
                        </div>

                        {ev.details && Object.keys(ev.details).length > 0 && (
                          <div className="text-[11px] bg-slate-950 p-2.5 rounded border border-slate-800/80 text-slate-300 space-y-1">
                            {Object.entries(ev.details).map(([k, v]) => (
                              <div key={k} className="flex justify-between gap-4">
                                <span className="text-slate-500 capitalize">{k.replace(/_/g, ' ')}:</span>
                                <span className="text-slate-200 break-all">{String(v)}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Cross Links */}
            {onNavigate && (
              <div className="pt-2 border-t border-slate-800 flex items-center gap-3">
                {selectedDetection.job_id && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setSelectedDetection(null)
                      onNavigate('deployments', { jobId: selectedDetection.job_id })
                    }}
                  >
                    Jump to Job Feed
                  </Button>
                )}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setSelectedDetection(null)
                    onNavigate('fleet', { agentId: selectedDetection.agent_id })
                  }}
                >
                  Jump to Agent
                </Button>
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  )
}
