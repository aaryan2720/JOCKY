import React from 'react'
import { Layers, Download, Filter } from 'lucide-react'
import { Card } from '../../components/common/Card'
import { Badge } from '../../components/common/Badge'
import { Button } from '../../components/common/Button'

export const ArtifactViewer: React.FC = () => {
  const MOCK_ARTIFACTS = [
    {
      id: 'art-001',
      type: 'process',
      agentId: 'agent-win-prod-01',
      collectedAt: '12:04:15 UTC',
      summary: 'powershell.exe (PID: 4812, Parent: wmiprvse.exe)',
      details: {
        pid: 4812,
        name: 'powershell.exe',
        path: 'C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe',
        command_line: 'powershell.exe -enc SQBFAFgA...',
        parent_pid: 1024,
        parent_name: 'wmiprvse.exe',
        sha256: '9f8377820823617302450...',
      },
    },
    {
      id: 'art-002',
      type: 'network',
      agentId: 'agent-win-prod-01',
      collectedAt: '12:04:16 UTC',
      summary: 'TCP 10.0.12.44:49182 -> 198.51.100.23:4444 (ESTABLISHED)',
      details: {
        proto: 'TCP',
        local_addr: '10.0.12.44',
        local_port: 49182,
        remote_addr: '198.51.100.23',
        remote_port: 4444,
        state: 'ESTABLISHED',
        pid: 4812,
      },
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 tracking-tight">Artifact Results</h2>
          <p className="text-sm text-slate-400 mt-1">
            Structured forensic evidence collected by Go agents during triage execution.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm">
            <Filter className="w-3.5 h-3.5" />
            Filter Types
          </Button>
          <Button variant="outline" size="sm">
            <Download className="w-3.5 h-3.5" />
            Export JSON
          </Button>
        </div>
      </div>

      <div className="space-y-4">
        {MOCK_ARTIFACTS.map((artifact) => (
          <Card key={artifact.id} className="p-4 border-slate-800 font-mono text-xs">
            <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800">
              <div className="flex items-center gap-3">
                <Badge variant="info">
                  <Layers className="w-3 h-3" />
                  {artifact.type.toUpperCase()}
                </Badge>
                <span className="text-slate-300 font-semibold">{artifact.summary}</span>
              </div>
              <div className="flex items-center gap-3 text-slate-500">
                <span>{artifact.agentId}</span>
                <span>•</span>
                <span>{artifact.collectedAt}</span>
              </div>
            </div>
            <div className="p-3 bg-[#0a0d14] rounded-lg border border-slate-900 text-slate-300 overflow-x-auto">
              <pre>{JSON.stringify(artifact.details, null, 2)}</pre>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
