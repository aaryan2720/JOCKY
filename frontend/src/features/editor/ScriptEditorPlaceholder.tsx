import React, { useState } from 'react'
import { Code2, Play, CheckCircle2, Sparkles, Layers } from 'lucide-react'
import { Card } from '../../components/common/Card'
import { Button } from '../../components/common/Button'
import { Badge } from '../../components/common/Badge'

const SAMPLE_SCRIPT = `// JOCKY Forensic Interrogation Query
TARGET os == "windows" AND tag == "workstation"

COLLECT processes
  WHERE name IN ["cmd.exe", "powershell.exe", "wscript.exe"]
  FILTER parent_name NOT IN ["explorer.exe", "services.exe"]
  WITH_HASH sha256

CHECK yara
  RULE "suspicious_obfuscated_powershell"
  ON process.command_line

COLLECT network_connections
  WHERE state == "ESTABLISHED" AND remote_port IN [4444, 1337, 8080]

ALERT IF detection.count > 0
  SEVERITY "HIGH"
  MESSAGE "Suspicious unsigned shell activity with non-standard parentage"
`

export const ScriptEditorPlaceholder: React.FC = () => {
  const [code, setCode] = useState(SAMPLE_SCRIPT)
  const [isValidated, setIsValidated] = useState(true)

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 tracking-tight">JOCKY Script Editor</h2>
          <p className="text-sm text-slate-400 mt-1">
            Author and validate forensic interrogation queries using the JOCKY DSL.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={() => setIsValidated(true)}>
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            Validate AST
          </Button>
          <Button variant="primary" size="sm">
            <Play className="w-3.5 h-3.5 fill-current" />
            Deploy to Fleet
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <Card className="p-0 overflow-hidden border-cyan-900/40">
            <div className="bg-[#0e1422] px-4 py-2.5 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-mono text-slate-300">
                <Code2 className="w-4 h-4 text-cyan-400" />
                <span>triage_suspicious_lineage.jky</span>
              </div>
              <Badge variant={isValidated ? 'success' : 'warning'}>
                {isValidated ? 'AST Valid' : 'Syntax Check Required'}
              </Badge>
            </div>
            <div className="p-4 bg-[#0a0d14]">
              <textarea
                value={code}
                onChange={(e) => setCode(e.target.value)}
                rows={16}
                className="w-full bg-transparent text-slate-100 font-mono text-sm leading-relaxed outline-none resize-none selection:bg-cyan-500/30"
                spellCheck={false}
              />
            </div>
          </Card>
        </div>

        <div className="space-y-4">
          <Card title="Query Compilation" subtitle="JOCKY AST & Execution Plan">
            <div className="space-y-4 text-xs font-mono">
              <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-800 space-y-2">
                <div className="flex items-center gap-2 text-cyan-400 font-semibold">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Pipeline Summary</span>
                </div>
                <div className="space-y-1 text-slate-400">
                  <p>Target: <span className="text-slate-200">os == "windows"</span></p>
                  <p>Collectors: <span className="text-slate-200">processes, network</span></p>
                  <p>Rules: <span className="text-slate-200">1 YARA scan</span></p>
                </div>
              </div>

              <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-800 space-y-2">
                <div className="flex items-center gap-2 text-blue-400 font-semibold">
                  <Layers className="w-3.5 h-3.5" />
                  <span>Targeted Endpoints</span>
                </div>
                <p className="text-slate-400">
                  Matches <span className="text-emerald-400 font-semibold">1</span> online agent in fleet.
                </p>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
