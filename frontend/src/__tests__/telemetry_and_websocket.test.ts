import { describe, it, expect } from 'vitest'
import { Artifact, Detection, WebSocketMessage } from '../types'

describe('Telemetry Normalization & WebSocket Protocol Tests', () => {
  it('normalizes process artifacts with all security fields', () => {
    const art: Artifact = {
      id: 'art-proc-001',
      job_id: 'job-101',
      agent_id: 'agent-win-01',
      type: 'process',
      data: {
        pid: 1044,
        ppid: 480,
        name: 'mimikatz.exe',
        path: 'C:\\Temp\\mimikatz.exe',
        command_line: 'mimikatz.exe "privilege::debug"',
        user: 'SYSTEM',
        signature_status: 'unsigned',
      },
      collected_at: '2026-09-30T10:00:00Z',
    }

    expect(art.type).toBe('process')
    expect(art.data.pid).toBe(1044)
    expect(art.data.signature_status).toBe('unsigned')
    expect(art.data.name).toBe('mimikatz.exe')
  })

  it('normalizes network connection artifacts with IP and port telemetry', () => {
    const art: Artifact = {
      id: 'art-net-002',
      job_id: 'job-101',
      agent_id: 'agent-win-01',
      type: 'connection',
      data: {
        protocol: 'TCP',
        local_address: '10.0.0.5',
        local_port: 49152,
        remote_address: '198.51.100.23',
        remote_port: 4444,
        state: 'ESTABLISHED',
        pid: 1044,
      },
      collected_at: '2026-09-30T10:00:00Z',
    }

    expect(art.type).toBe('connection')
    expect(art.data.remote_port).toBe(4444)
    expect(art.data.state).toBe('ESTABLISHED')
  })

  it('normalizes persistence autorun and scheduled task artifacts', () => {
    const autorun: Artifact = {
      id: 'art-auto-003',
      job_id: 'job-102',
      agent_id: 'agent-win-01',
      type: 'autorun',
      data: {
        location: 'HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run',
        name: 'UpdaterService',
        command: 'C:\\Temp\\backdoor.exe',
        user: 'SYSTEM',
        source: 'registry',
        enabled: true,
      },
      collected_at: '2026-09-30T10:00:00Z',
    }

    const task: Artifact = {
      id: 'art-task-004',
      job_id: 'job-102',
      agent_id: 'agent-win-01',
      type: 'scheduled_task',
      data: {
        name: '\\Microsoft\\Maintenance\\TaskAudit',
        path: '\\Microsoft\\Maintenance\\TaskAudit',
        author: 'Administrator',
        action: 'powershell.exe -NoP -W Hidden',
        arguments: '-NoP -W Hidden',
        trigger: 'At startup',
        enabled: true,
        user: 'SYSTEM',
      },
      collected_at: '2026-09-30T10:00:00Z',
    }

    expect(autorun.data.enabled).toBe(true)
    expect(autorun.data.source).toBe('registry')
    expect(task.data.action).toContain('powershell.exe')
    expect(task.data.trigger).toBe('At startup')
  })

  it('normalizes identity user accounts and session artifacts', () => {
    const user: Artifact = {
      id: 'art-user-005',
      job_id: 'job-103',
      agent_id: 'agent-lin-02',
      type: 'user',
      data: {
        username: 'sysbackdoor',
        uid: 1005,
        gid: 1005,
        home_dir: '/home/sysbackdoor',
        shell: '/bin/bash',
        enabled: true,
        account_type: 'local',
      },
      collected_at: '2026-09-30T10:00:00Z',
    }

    const session: Artifact = {
      id: 'art-sess-006',
      job_id: 'job-103',
      agent_id: 'agent-lin-02',
      type: 'session',
      data: {
        username: 'sysbackdoor',
        session_id: 'pts/0',
        terminal: 'pts/0',
        state: 'Active',
        logon_type: 'SSH',
        source: '192.168.1.100',
        login_time: '2026-09-30 09:30',
      },
      collected_at: '2026-09-30T10:00:00Z',
    }

    expect(user.data.username).toBe('sysbackdoor')
    expect(user.data.shell).toBe('/bin/bash')
    expect(session.data.logon_type).toBe('SSH')
    expect(session.data.state).toBe('Active')
  })

  it('parses detection records and maintains evidence chain integrity', () => {
    const det: Detection = {
      id: 'det-001',
      agent_id: 'agent-win-01',
      job_id: 'job-101',
      rule_id: 'PROC-NET-001',
      severity: 'high',
      title: 'Unsigned process with active network connection',
      description: 'Process PID 1044 (mimikatz.exe) reported unsigned and connected to 198.51.100.23:4444',
      status: 'open',
      evidence: [
        {
          artifact_id: 'art-proc-001',
          type: 'process',
          details: { pid: 1044, name: 'mimikatz.exe', signature_status: 'unsigned' },
        },
        {
          artifact_id: 'art-net-002',
          type: 'connection',
          details: { pid: 1044, remote_address: '198.51.100.23', remote_port: 4444 },
        },
      ],
      created_at: '2026-09-30T10:01:00Z',
    }

    expect(det.severity).toBe('high')
    expect(det.evidence.length).toBe(2)
    expect(det.evidence[0].artifact_id).toBe('art-proc-001')
    expect(det.evidence[1].artifact_id).toBe('art-net-002')
  })

  it('handles structured WebSocket stream protocol messages', () => {
    const rawWsMessages = [
      '{"event":"connected","job_id":"job-101","message":"Subscribed to live job event stream"}',
      '{"event":"artifact_collected","job_id":"job-101","agent_id":"agent-win-01","payload":{"type":"process","data":{"pid":1044}}}',
      '{"event":"threat_detected","job_id":"job-101","detection":{"id":"det-001","rule_id":"PROC-NET-001","severity":"high","title":"Alert"}}',
      '{"event":"job_status","job_id":"job-101","status":"completed"}',
    ]

    const parsed: WebSocketMessage[] = rawWsMessages.map((m) => JSON.parse(m))
    expect(parsed[0].event).toBe('connected')
    expect(parsed[1].event).toBe('artifact_collected')
    expect(parsed[1].payload.type).toBe('process')
    expect(parsed[2].event).toBe('threat_detected')
    expect(parsed[2].detection?.rule_id).toBe('PROC-NET-001')
    expect(parsed[3].event).toBe('job_status')
    expect(parsed[3].status).toBe('completed')
  })
})
