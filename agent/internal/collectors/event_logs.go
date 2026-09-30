package collectors

import (
	"context"
	"encoding/json"
	"encoding/xml"
	"fmt"
	"strconv"
	"strings"
	"time"
)

const (
	DefaultMaxEvents     = 500
	DefaultMaxMsgSize    = 4096
	DefaultEventChannel  = "System"
)

// EventLogEntry represents a normalized forensic event log record.
type EventLogEntry struct {
	Channel   string `json:"channel"`
	EventID   int64  `json:"event_id"`
	Provider  string `json:"provider"`
	Level     string `json:"level"`
	Timestamp string `json:"timestamp"`
	RecordID  int64  `json:"record_id"`
	Computer  string `json:"computer"`
	Message   string `json:"message"`
	Source    string `json:"source"` // "wevtutil", "powershell", "journald", "syslog"
}

// EventLogCollector enumerates Windows Event Logs and Linux system journals / syslogs in a strictly read-only manner.
type EventLogCollector struct {
	MaxEvents      int
	MaxMessageSize int
}

// NewEventLogCollector creates an initialized EventLogCollector with safe default bounds.
func NewEventLogCollector() *EventLogCollector {
	return &EventLogCollector{
		MaxEvents:      DefaultMaxEvents,
		MaxMessageSize: DefaultMaxMsgSize,
	}
}

func (c *EventLogCollector) Name() string {
	return "event_logs"
}

func (c *EventLogCollector) Supports(target string) bool {
	t := strings.ToLower(strings.TrimSpace(target))
	return t == "event_logs" || t == "event_log" || t == "events" || t == "event" || t == "logs" || t == "syslog" || t == "journald"
}

// Collect reads event logs within bounded limits without modifying, clearing, or subscribing to logs.
func (c *EventLogCollector) Collect(ctx context.Context, request CollectionRequest) ([]Artifact, error) {
	if ctx.Err() != nil {
		return nil, ctx.Err()
	}

	maxEvents := c.MaxEvents
	maxMsgSize := c.MaxMessageSize
	channel := DefaultEventChannel

	if request.Parameters != nil {
		if me, ok := request.Parameters["max_events"].(int); ok && me > 0 {
			maxEvents = me
		}
		if lim, ok := request.Parameters["limit"].(int); ok && lim > 0 {
			maxEvents = lim
		}
		if mms, ok := request.Parameters["max_message_size"].(int); ok && mms > 0 {
			maxMsgSize = mms
		}
		if ch, ok := request.Parameters["channel"].(string); ok && ch != "" {
			channel = ch
		} else if ln, ok := request.Parameters["log_name"].(string); ok && ln != "" {
			channel = ln
		}
	}

	opts := map[string]interface{}{
		"max_events":         maxEvents,
		"max_message_size":    maxMsgSize,
		"channel":            channel,
	}

	entries, err := collectEventLogs(ctx, opts)
	if err != nil {
		return nil, err
	}

	now := time.Now().UTC()
	artifacts := make([]Artifact, 0, len(entries))
	for _, e := range entries {
		msg := e.Message
		if maxMsgSize > 0 && len(msg) > maxMsgSize {
			msg = msg[:maxMsgSize] + "... [truncated]"
		}

		artifacts = append(artifacts, Artifact{
			JobID:       request.JobID,
			AgentID:     request.AgentID,
			Type:        "event",
			CollectedAt: now,
			Data: map[string]interface{}{
				"channel":   e.Channel,
				"event_id":  e.EventID,
				"provider":  e.Provider,
				"level":     e.Level,
				"timestamp": e.Timestamp,
				"record_id": e.RecordID,
				"computer":  e.Computer,
				"message":   msg,
				"source":    e.Source,
			},
		})
	}

	return artifacts, nil
}

// Windows Event Log XML Structures for wevtutil /f:xml / RenderedXml
type wevtutilEventsXML struct {
	XMLName xml.Name          `xml:"Events"`
	Events  []wevtutilEventXML `xml:"Event"`
}

type wevtutilEventXML struct {
	System struct {
		Provider struct {
			Name string `xml:"Name,attr"`
		} `xml:"Provider"`
		EventID       int64  `xml:"EventID"`
		Level         int    `xml:"Level"`
		TimeCreated   struct {
			SystemTime string `xml:"SystemTime,attr"`
		} `xml:"TimeCreated"`
		EventRecordID int64  `xml:"EventRecordID"`
		Channel       string `xml:"Channel"`
		Computer      string `xml:"Computer"`
	} `xml:"System"`
	RenderingInfo struct {
		Message string `xml:"Message"`
		Level   string `xml:"Level"`
	} `xml:"RenderingInfo"`
	EventData struct {
		Data []string `xml:"Data"`
	} `xml:"EventData"`
}

// LevelToName maps Windows Event level numeric IDs to human-readable names.
func LevelToName(level int) string {
	switch level {
	case 1:
		return "Critical"
	case 2:
		return "Error"
	case 3:
		return "Warning"
	case 4:
		return "Information"
	case 5:
		return "Verbose"
	default:
		return "Information"
	}
}

// SyslogPriorityToLevel maps Linux syslog / journald priority (0-7) to normalized severity.
func SyslogPriorityToLevel(p int) string {
	switch p {
	case 0:
		return "Emergency"
	case 1:
		return "Alert"
	case 2:
		return "Critical"
	case 3:
		return "Error"
	case 4:
		return "Warning"
	case 5:
		return "Notice"
	case 6:
		return "Information"
	case 7:
		return "Debug"
	default:
		return "Information"
	}
}

// ParseWevtutilXML parses Windows wevtutil XML or RenderedXml output into normalized EventLogEntry list.
func ParseWevtutilXML(xmlData string, maxEvents int, maxMsgSize int) []EventLogEntry {
	var entries []EventLogEntry
	if strings.TrimSpace(xmlData) == "" {
		return entries
	}

	// Wrap in root tag if single event or raw sequence
	wrapped := xmlData
	if !strings.HasPrefix(strings.TrimSpace(xmlData), "<Events") {
		wrapped = "<Events>" + xmlData + "</Events>"
	}

	var root wevtutilEventsXML
	if err := xml.Unmarshal([]byte(wrapped), &root); err != nil {
		// Try parsing event-by-event with a decoder
		decoder := xml.NewDecoder(strings.NewReader(wrapped))
		for {
			var ev wevtutilEventXML
			if err := decoder.Decode(&ev); err != nil {
				break
			}
			entry := convertXMLEventToEntry(ev, maxMsgSize)
			if entry != nil {
				entries = append(entries, *entry)
				if maxEvents > 0 && len(entries) >= maxEvents {
					return entries
				}
			}
		}
		return entries
	}

	for _, ev := range root.Events {
		entry := convertXMLEventToEntry(ev, maxMsgSize)
		if entry != nil {
			entries = append(entries, *entry)
			if maxEvents > 0 && len(entries) >= maxEvents {
				break
			}
		}
	}

	return entries
}

func convertXMLEventToEntry(ev wevtutilEventXML, maxMsgSize int) *EventLogEntry {
	if ev.System.EventID == 0 && ev.System.Provider.Name == "" && ev.System.Channel == "" {
		return nil
	}

	level := ev.RenderingInfo.Level
	if level == "" {
		level = LevelToName(ev.System.Level)
	}

	msg := ev.RenderingInfo.Message
	if msg == "" && len(ev.EventData.Data) > 0 {
		msg = strings.Join(ev.EventData.Data, " ")
	}
	if maxMsgSize > 0 && len(msg) > maxMsgSize {
		msg = msg[:maxMsgSize] + "... [truncated]"
	}

	ch := ev.System.Channel
	if ch == "" {
		ch = DefaultEventChannel
	}

	return &EventLogEntry{
		Channel:   ch,
		EventID:   ev.System.EventID,
		Provider:  ev.System.Provider.Name,
		Level:     level,
		Timestamp: ev.System.TimeCreated.SystemTime,
		RecordID:  ev.System.EventRecordID,
		Computer:  ev.System.Computer,
		Message:   msg,
		Source:    "wevtutil",
	}
}

// ParseJournaldJSON parses line-delimited JSON output from `journalctl -o json`.
func ParseJournaldJSON(output string, maxEvents int, maxMsgSize int) []EventLogEntry {
	var entries []EventLogEntry
	lines := strings.Split(output, "\n")

	for _, line := range lines {
		trimmed := strings.TrimSpace(line)
		if trimmed == "" || !strings.HasPrefix(trimmed, "{") {
			continue
		}

		var raw map[string]interface{}
		if err := json.Unmarshal([]byte(trimmed), &raw); err != nil {
			continue
		}

		// Extract timestamp
		timestamp := ""
		if tsMicro, ok := raw["__REALTIME_TIMESTAMP"].(string); ok {
			if microVal, err := strconv.ParseInt(tsMicro, 10, 64); err == nil {
				timestamp = time.Unix(0, microVal*1000).UTC().Format(time.RFC3339)
			}
		} else if tsMicroNum, ok := raw["__REALTIME_TIMESTAMP"].(float64); ok {
			timestamp = time.Unix(0, int64(tsMicroNum)*1000).UTC().Format(time.RFC3339)
		}
		if timestamp == "" {
			timestamp = time.Now().UTC().Format(time.RFC3339)
		}

		// Provider / Unit
		provider := ""
		if unit, ok := raw["_SYSTEMD_UNIT"].(string); ok && unit != "" {
			provider = unit
		} else if ident, ok := raw["SYSLOG_IDENTIFIER"].(string); ok && ident != "" {
			provider = ident
		} else if comm, ok := raw["_COMM"].(string); ok && comm != "" {
			provider = comm
		}

		// Computer / Host
		computer := ""
		if host, ok := raw["_HOSTNAME"].(string); ok {
			computer = host
		}

		// Level / Priority
		level := "Information"
		if prioStr, ok := raw["PRIORITY"].(string); ok {
			if p, err := strconv.Atoi(prioStr); err == nil {
				level = SyslogPriorityToLevel(p)
			}
		} else if prioNum, ok := raw["PRIORITY"].(float64); ok {
			level = SyslogPriorityToLevel(int(prioNum))
		}

		// Message
		message := ""
		if msg, ok := raw["MESSAGE"].(string); ok {
			message = msg
		}
		if maxMsgSize > 0 && len(message) > maxMsgSize {
			message = message[:maxMsgSize] + "... [truncated]"
		}

		// Record ID (Cursor hash or PID)
		var recordID int64
		if pidStr, ok := raw["_PID"].(string); ok {
			if pid, err := strconv.ParseInt(pidStr, 10, 64); err == nil {
				recordID = pid
			}
		}

		entries = append(entries, EventLogEntry{
			Channel:   "journald",
			EventID:   0,
			Provider:  provider,
			Level:     level,
			Timestamp: timestamp,
			RecordID:  recordID,
			Computer:  computer,
			Message:   message,
			Source:    "journald",
		})

		if maxEvents > 0 && len(entries) >= maxEvents {
			break
		}
	}

	return entries
}

// ParseSyslogContent parses standard RFC 3164 / RFC 5424 syslog file content.
func ParseSyslogContent(content string, channel string, maxEvents int, maxMsgSize int) []EventLogEntry {
	var entries []EventLogEntry
	lines := strings.Split(content, "\n")

	for _, line := range lines {
		trimmed := strings.TrimSpace(line)
		if trimmed == "" || strings.HasPrefix(trimmed, "#") {
			continue
		}

		fields := strings.Fields(trimmed)
		if len(fields) < 4 {
			continue
		}

		// Format 1: "Oct 11 22:14:15 hostname process[1234]: message..."
		// Format 2: "2026-09-30T10:00:00.000000+00:00 hostname process[1234]: message..."
		var timestamp, computer, provider, message string

		if strings.Contains(fields[0], "T") || strings.Contains(fields[0], "-") {
			// ISO format timestamp
			timestamp = fields[0]
			if len(fields) >= 3 {
				computer = fields[1]
				procAndMsg := fields[2:]
				provider = strings.TrimSuffix(procAndMsg[0], ":")
				if len(procAndMsg) > 1 {
					message = strings.Join(procAndMsg[1:], " ")
				}
			}
		} else if len(fields) >= 5 {
			// Traditional syslog format: Month Day Time Host Proc: Msg
			timestamp = fmt.Sprintf("%s %s %s", fields[0], fields[1], fields[2])
			computer = fields[3]
			procAndMsg := fields[4:]
			provider = strings.TrimSuffix(procAndMsg[0], ":")
			if len(procAndMsg) > 1 {
				message = strings.Join(procAndMsg[1:], " ")
			}
		} else {
			message = trimmed
		}

		if maxMsgSize > 0 && len(message) > maxMsgSize {
			message = message[:maxMsgSize] + "... [truncated]"
		}

		entries = append(entries, EventLogEntry{
			Channel:   channel,
			EventID:   0,
			Provider:  provider,
			Level:     "Information",
			Timestamp: timestamp,
			RecordID:  int64(len(entries) + 1),
			Computer:  computer,
			Message:   message,
			Source:    "syslog",
		})

		if maxEvents > 0 && len(entries) >= maxEvents {
			break
		}
	}

	return entries
}
