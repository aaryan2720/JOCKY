import React from 'react'
import { ShieldAlert, ChevronRight } from 'lucide-react'
import { Card } from '../../components/common/Card'
import { Badge } from '../../components/common/Badge'
import { Button } from '../../components/common/Button'

export const ThreatAlertList: React.FC = () => {
  const MOCK_THREATS = [
    {
      id: 'det-1024',
      rule: 'Suspicious_PowerShell_Parentage',
      severity: 'HIGH' as const,
      agentId: 'agent-win-prod-01',
      hostname: 'SEC-FIN-WIN11',
      detectedAt: '12:04:18 UTC',
      explanation:
        'PowerShell process spawned directly from WMI Provider Host (wmiprvse.exe) establishing outbound connection to non-standard remote port 4444.',
      mitre: 'T1047 (WMI), T1059.001 (PowerShell)',
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 tracking-tight">Threat Detections</h2>
          <p className="text-sm text-slate-400 mt-1">
            Correlated threat anomalies and rule violations identified across fleet telemetry.
          </p>
        </div>
      </div>

      <div className="space-y-4">
        {MOCK_THREATS.map((threat) => (
          <Card
            key={threat.id}
            className="border-rose-900/40 bg-gradient-to-r from-rose-950/10 via-[#111726]/80 to-[#111726]/80"
          >
            <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-lg bg-rose-950/60 border border-rose-800/60 flex items-center justify-center text-rose-400 shrink-0">
                  <ShieldAlert className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-3">
                    <span className="text-base font-bold text-slate-100">{threat.rule}</span>
                    <Badge variant="danger">{threat.severity}</Badge>
                    <span className="text-xs font-mono text-slate-400">MITRE: {threat.mitre}</span>
                  </div>
                  <p className="text-sm text-slate-300 mt-2 leading-relaxed">
                    {threat.explanation}
                  </p>
                  <div className="flex items-center gap-4 text-xs font-mono text-slate-400 mt-3">
                    <span>Host: <span className="text-cyan-400">{threat.hostname}</span></span>
                    <span>Agent: {threat.agentId}</span>
                    <span>Detected: {threat.detectedAt}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 self-end sm:self-center shrink-0">
                <Button variant="outline" size="sm">
                  Investigate
                  <ChevronRight className="w-3.5 h-3.5" />
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
