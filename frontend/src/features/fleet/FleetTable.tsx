import React from 'react'
import { Server, Terminal, Shield, RefreshCw } from 'lucide-react'
import { Card } from '../../components/common/Card'
import { Badge } from '../../components/common/Badge'
import { Button } from '../../components/common/Button'
import { Agent } from '../../types'

const MOCK_AGENTS: Agent[] = [
  {
    id: 'agent-win-prod-01',
    hostname: 'SEC-FIN-WIN11',
    os: 'windows',
    ip_address: '10.0.12.44',
    status: 'online',
    version: '0.1.0',
    tags: ['workstation', 'finance', 'prod'],
    last_seen: 'Just now',
  },
  {
    id: 'agent-lin-srv-02',
    hostname: 'PROD-KUBE-NODE-01',
    os: 'linux',
    ip_address: '10.0.24.102',
    status: 'online',
    version: '0.1.0',
    tags: ['server', 'kubernetes', 'infrastructure'],
    last_seen: '2 mins ago',
  },
]

export const FleetTable: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 tracking-tight">Fleet Overview</h2>
          <p className="text-sm text-slate-400 mt-1">
            Real-time status of enrolled cross-platform forensic agents.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm">
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </Button>
          <Button variant="primary" size="sm">
            Enroll New Agent
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-400">Total Enrolled</p>
              <p className="text-2xl font-bold text-slate-100 mt-1">2</p>
            </div>
            <div className="w-10 h-10 rounded-lg bg-cyan-950/40 border border-cyan-800/40 flex items-center justify-center text-cyan-400">
              <Server className="w-5 h-5" />
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-400">Active Heartbeats</p>
              <p className="text-2xl font-bold text-emerald-400 mt-1">2</p>
            </div>
            <div className="w-10 h-10 rounded-lg bg-emerald-950/40 border border-emerald-800/40 flex items-center justify-center text-emerald-400">
              <Shield className="w-5 h-5" />
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-400">Target Coverage</p>
              <p className="text-2xl font-bold text-cyan-400 mt-1">100%</p>
            </div>
            <div className="w-10 h-10 rounded-lg bg-blue-950/40 border border-blue-800/40 flex items-center justify-center text-blue-400">
              <Terminal className="w-5 h-5" />
            </div>
          </div>
        </Card>
      </div>

      <Card>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 text-xs uppercase tracking-wider font-mono">
                <th className="py-3 px-4">Agent ID</th>
                <th className="py-3 px-4">Hostname</th>
                <th className="py-3 px-4">Platform</th>
                <th className="py-3 px-4">IP Address</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Tags</th>
                <th className="py-3 px-4">Last Seen</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
              {MOCK_AGENTS.map((agent) => (
                <tr key={agent.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-3.5 px-4 font-semibold text-cyan-400">{agent.id}</td>
                  <td className="py-3.5 px-4 text-slate-200">{agent.hostname}</td>
                  <td className="py-3.5 px-4">
                    <span className="capitalize text-slate-300">{agent.os}</span>
                  </td>
                  <td className="py-3.5 px-4 text-slate-400">{agent.ip_address}</td>
                  <td className="py-3.5 px-4">
                    <Badge variant={agent.status === 'online' ? 'success' : 'danger'}>
                      {agent.status}
                    </Badge>
                  </td>
                  <td className="py-3.5 px-4">
                    <div className="flex gap-1.5">
                      {agent.tags.map((tag) => (
                        <span key={tag} className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                          {tag}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="py-3.5 px-4 text-slate-400">{agent.last_seen}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}
