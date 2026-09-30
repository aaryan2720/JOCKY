import React, { useEffect, useState } from 'react'
import {
  Code2,
  Play,
  CheckCircle,
  AlertCircle,
  Server,
  Sparkles,
  ArrowRight,
  ShieldCheck,
} from 'lucide-react'
import { Card } from '../../components/common/Card'
import { Badge } from '../../components/common/Badge'
import { Button } from '../../components/common/Button'
import { ErrorBanner } from '../../components/common/ErrorBanner'
import { fetchAgents, fetchScripts, validateScript, createJob } from '../../api'
import { Agent, JockyScript, ScriptValidateResponse } from '../../types'
import { NavTab } from '../../components/layout/Sidebar'

interface ScriptEditorProps {
  initialAgentId?: string
  onNavigate?: (tab: NavTab, context?: { jobId?: string; agentId?: string }) => void
}

const DEFAULT_SCRIPT = `COLLECT autoruns;
COLLECT scheduled_tasks;
COLLECT users;
COLLECT sessions;`

export const ScriptEditor: React.FC<ScriptEditorProps> = ({ initialAgentId, onNavigate }) => {
  const [scriptBody, setScriptBody] = useState(DEFAULT_SCRIPT)
  const [agents, setAgents] = useState<Agent[]>([])
  const [selectedAgentIds, setSelectedAgentIds] = useState<string[]>([])
  const [templates, setTemplates] = useState<JockyScript[]>([])
  const [isValidating, setIsValidating] = useState(false)
  const [validationResult, setValidationResult] = useState<ScriptValidateResponse | null>(null)
  const [isDispatching, setIsDispatching] = useState(false)
  const [dispatchError, setDispatchError] = useState<string | null>(null)
  const [dispatchedJobId, setDispatchedJobId] = useState<string | null>(null)

  useEffect(() => {
    fetchAgents().then((res) => {
      const items = res.items || []
      setAgents(items)
      if (initialAgentId && items.some((a) => a.id === initialAgentId)) {
        setSelectedAgentIds([initialAgentId])
      } else if (items.length > 0) {
        setSelectedAgentIds([items[0].id])
      }
    })

    fetchScripts().then((res) => {
      setTemplates(res || [])
    })
  }, [initialAgentId])

  const handleValidate = async () => {
    setIsValidating(true)
    setValidationResult(null)
    setDispatchError(null)
    try {
      const res = await validateScript(scriptBody)
      setValidationResult(res)
    } catch (err: any) {
      setValidationResult({
        valid: false,
        estimated_artifacts: [],
        errors: [err.message || 'Validation request failed.'],
      })
    } finally {
      setIsValidating(false)
    }
  }

  const handleDispatch = async () => {
    if (selectedAgentIds.length === 0) {
      setDispatchError('Please select at least one target agent for execution.')
      return
    }

    setIsDispatching(true)
    setDispatchError(null)
    setDispatchedJobId(null)

    try {
      const res = await createJob({
        script_body: scriptBody,
        target_agent_ids: selectedAgentIds,
      })
      setDispatchedJobId(res.job_id)
    } catch (err: any) {
      setDispatchError(err.message || 'Failed to dispatch forensic investigation job.')
    } finally {
      setIsDispatching(false)
    }
  }

  const handleSelectTemplate = (template: JockyScript) => {
    setScriptBody(template.body)
    setValidationResult(null)
    setDispatchedJobId(null)
  }

  const toggleAgent = (agentId: string) => {
    setSelectedAgentIds((prev) =>
      prev.includes(agentId) ? prev.filter((id) => id !== agentId) : [...prev, agentId]
    )
  }

  const selectAllAgents = () => {
    if (selectedAgentIds.length === agents.length) {
      setSelectedAgentIds([])
    } else {
      setSelectedAgentIds(agents.map((a) => a.id))
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 tracking-tight">JOCKY Investigation Editor</h1>
          <p className="text-sm text-slate-400 mt-1">
            Author and dispatch structured, read-only forensic inspection plans to endpoint agents.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={handleValidate} disabled={isValidating}>
            <CheckCircle className="w-3.5 h-3.5" />
            {isValidating ? 'Validating...' : 'Validate DSL'}
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleDispatch}
            disabled={isDispatching || selectedAgentIds.length === 0}
          >
            <Play className="w-3.5 h-3.5" />
            {isDispatching ? 'Dispatching...' : 'Execute Investigation'}
          </Button>
        </div>
      </div>

      {dispatchError && <ErrorBanner message={dispatchError} onRetry={handleDispatch} />}

      {/* Dispatched Success Banner */}
      {dispatchedJobId && (
        <div className="p-4 rounded-xl bg-emerald-950/40 border border-emerald-800/60 text-emerald-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-lg shadow-emerald-950/30">
          <div className="flex items-center gap-3">
            <CheckCircle className="w-5 h-5 text-emerald-400 shrink-0" />
            <div>
              <h4 className="text-sm font-semibold text-emerald-300">
                Investigation Dispatched Successfully!
              </h4>
              <p className="text-xs text-emerald-400/90 font-mono mt-0.5">
                Job ID: <span className="font-bold text-white">{dispatchedJobId}</span> dispatches to {selectedAgentIds.length} agent(s).
              </p>
            </div>
          </div>
          {onNavigate && (
            <Button
              variant="primary"
              size="sm"
              onClick={() => onNavigate('deployments', { jobId: dispatchedJobId })}
              className="shrink-0"
            >
              Monitor Live Job Feed
              <ArrowRight className="w-3.5 h-3.5 ml-1" />
            </Button>
          )}
        </div>
      )}

      {/* Template Quick Select Bar */}
      {templates.length > 0 && (
        <Card className="p-3">
          <div className="flex items-center gap-2 mb-2 text-xs font-mono text-slate-400">
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            <span>Forensic Templates:</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {templates.map((tpl) => (
              <button
                key={tpl.id}
                onClick={() => handleSelectTemplate(tpl)}
                className="px-2.5 py-1 text-xs rounded-md bg-slate-900 border border-slate-800 hover:border-cyan-800/60 hover:text-cyan-400 text-slate-300 font-mono transition-colors text-left"
              >
                {tpl.name}
              </button>
            ))}
          </div>
        </Card>
      )}

      {/* Main Grid: Script Editor + Target Fleet Selection */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Editor Area (2 cols) */}
        <div className="lg:col-span-2 space-y-4">
          <Card className="p-0 overflow-hidden border-slate-800 focus-within:border-cyan-800/80 transition-colors">
            <div className="px-4 py-2.5 bg-slate-900/80 border-b border-slate-800 flex items-center justify-between font-mono text-xs text-slate-400">
              <div className="flex items-center gap-2">
                <Code2 className="w-4 h-4 text-cyan-400" />
                <span>forensic_investigation.jocky</span>
              </div>
              <span className="text-[11px] text-slate-500">JOCKY v1.0 DSL</span>
            </div>
            <textarea
              value={scriptBody}
              onChange={(e) => {
                setScriptBody(e.target.value)
                setValidationResult(null)
              }}
              rows={14}
              placeholder="COLLECT processes; ...\nCOLLECT autoruns; ..."
              className="w-full p-4 bg-[#0a0d14] text-slate-200 font-mono text-sm leading-relaxed resize-y focus:outline-none placeholder-slate-700 selection:bg-cyan-900/50"
              spellCheck={false}
            />
          </Card>

          {/* Validation Feedback Card */}
          {validationResult && (
            <Card
              className={`p-4 font-mono text-xs ${
                validationResult.valid
                  ? 'bg-emerald-950/20 border-emerald-800/50 text-emerald-300'
                  : 'bg-rose-950/20 border-rose-800/50 text-rose-300'
              }`}
            >
              <div className="flex items-start gap-2.5">
                {validationResult.valid ? (
                  <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                )}
                <div className="space-y-1.5 flex-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold">
                      {validationResult.valid ? 'Valid Execution Plan' : 'DSL Syntax Error'}
                    </span>
                    {validationResult.ast_summary?.plan_version && (
                      <span className="text-[10px] text-slate-400">
                        Plan Version: {validationResult.ast_summary.plan_version}
                      </span>
                    )}
                  </div>

                  {validationResult.valid ? (
                    <div className="space-y-1 text-[11px] text-slate-400">
                      <p>
                        Statements parsed: {validationResult.ast_summary?.statements || 0}
                      </p>
                      {validationResult.estimated_artifacts.length > 0 && (
                        <div className="flex items-center gap-1.5 flex-wrap pt-1">
                          <span className="text-slate-500">Collectors to trigger:</span>
                          {validationResult.estimated_artifacts.map((art) => (
                            <span
                              key={art}
                              className="px-1.5 py-0.5 rounded bg-emerald-900/40 text-emerald-300 border border-emerald-700/50 text-[10px]"
                            >
                              {art}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="space-y-1 text-[11px] text-rose-300">
                      {validationResult.errors.map((err, i) => (
                        <p key={i}>{err}</p>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </Card>
          )}

          {/* Defensive Safety Notice */}
          <div className="flex items-center gap-2 text-xs text-slate-500 font-mono px-2">
            <ShieldCheck className="w-4 h-4 text-cyan-400 shrink-0" />
            <span>
              Defensive Safety: Scripts compile into deterministic, read-only plan envelopes. Arbitrary shell execution is disabled.
            </span>
          </div>
        </div>

        {/* Target Fleet Selection (1 col) */}
        <div className="space-y-4">
          <Card className="space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Server className="w-4 h-4 text-cyan-400" />
                <h3 className="text-sm font-semibold text-slate-200 font-mono">Target Agents</h3>
              </div>
              <button
                onClick={selectAllAgents}
                className="text-xs text-cyan-400 hover:text-cyan-300 font-mono"
              >
                {selectedAgentIds.length === agents.length ? 'Deselect All' : 'Select All'}
              </button>
            </div>

            {agents.length === 0 ? (
              <p className="text-xs text-slate-500 py-4 text-center">No registered agents available.</p>
            ) : (
              <div className="space-y-2 max-h-[360px] overflow-y-auto pr-1">
                {agents.map((agent) => {
                  const isChecked = selectedAgentIds.includes(agent.id)
                  return (
                    <div
                      key={agent.id}
                      onClick={() => toggleAgent(agent.id)}
                      className={`p-3 rounded-lg border text-xs font-mono transition-colors cursor-pointer flex items-center justify-between ${
                        isChecked
                          ? 'bg-cyan-950/30 border-cyan-800/60 text-slate-200'
                          : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700'
                      }`}
                    >
                      <div className="space-y-0.5">
                        <div className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            checked={isChecked}
                            onChange={() => {}}
                            className="rounded border-slate-700 text-cyan-500 focus:ring-0"
                          />
                          <span className="font-semibold text-slate-200">{agent.hostname}</span>
                        </div>
                        <span className="text-[10px] text-slate-500 pl-5 block">{agent.id}</span>
                      </div>
                      <Badge variant={agent.status === 'online' ? 'success' : 'danger'}>
                        {agent.os}
                      </Badge>
                    </div>
                  )
                })}
              </div>
            )}

            <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400 font-mono">
              <span>Selected for dispatch:</span>
              <span className="font-bold text-cyan-400">{selectedAgentIds.length} agent(s)</span>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
