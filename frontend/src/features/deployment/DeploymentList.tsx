import React from 'react'
import { Rocket, Clock, CheckCircle, AlertCircle } from 'lucide-react'
import { Card } from '../../components/common/Card'
import { Badge } from '../../components/common/Badge'
import { Button } from '../../components/common/Button'

export const DeploymentList: React.FC = () => {
  const MOCK_JOBS = [
    {
      id: 'job-984210',
      scriptName: 'triage_suspicious_lineage.jky',
      targetCount: 1,
      status: 'completed',
      startedAt: '10 mins ago',
      artifactsCollected: 14,
      detectionsCount: 1,
    },
    {
      id: 'job-984209',
      scriptName: 'hunt_persistence_autoruns.jky',
      targetCount: 2,
      status: 'completed',
      startedAt: '45 mins ago',
      artifactsCollected: 58,
      detectionsCount: 0,
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 tracking-tight">Deployments & Jobs</h2>
          <p className="text-sm text-slate-400 mt-1">
            Track forensic interrogation jobs dispatched across fleet nodes.
          </p>
        </div>
        <Button variant="primary" size="sm">
          <Rocket className="w-3.5 h-3.5" />
          Dispatch New Job
        </Button>
      </div>

      <div className="space-y-3">
        {MOCK_JOBS.map((job) => (
          <Card key={job.id} className="hover:border-slate-700 transition-all">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-start gap-3">
                <div className="w-9 h-9 rounded-lg bg-cyan-950/50 border border-cyan-800/40 flex items-center justify-center text-cyan-400 shrink-0 mt-0.5">
                  <Rocket className="w-4 h-4" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-100">{job.scriptName}</span>
                    <span className="text-xs font-mono text-cyan-400">({job.id})</span>
                  </div>
                  <div className="flex items-center gap-4 text-xs text-slate-400 mt-1">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {job.startedAt}
                    </span>
                    <span>Target Agents: {job.targetCount}</span>
                    <span>Artifacts: {job.artifactsCollected}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3 self-end sm:self-center">
                {job.detectionsCount > 0 ? (
                  <Badge variant="danger">
                    <AlertCircle className="w-3 h-3" />
                    {job.detectionsCount} Threat Detected
                  </Badge>
                ) : (
                  <Badge variant="success">
                    <CheckCircle className="w-3 h-3" />
                    Clean
                  </Badge>
                )}
                <Button variant="outline" size="sm">
                  View Details
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
