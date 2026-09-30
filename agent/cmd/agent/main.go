package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"

	"github.com/jocky-dfir/jocky/agent/internal/registration"
	"github.com/jocky-dfir/jocky/agent/internal/runtime"
	"github.com/jocky-dfir/jocky/agent/internal/transport"
)

const (
	Version = "0.1.0"
)

func main() {
	// Standard startup log required by JOCKY specification
	fmt.Println("JOCKY agent starting")
	log.Printf("[JOCKY Agent v%s] Initializing forensic runtime...", Version)

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Handle OS shutdown signals gracefully
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)

	serverURL := os.Getenv("AGENT_SERVER_URL")
	if serverURL == "" {
		serverURL = "http://localhost:8000"
	}

	token := os.Getenv("AGENT_REGISTRATION_TOKEN")
	if token == "" {
		token = "jocky-agent-insecure-dev-token"
	}

	httpTransport := transport.NewHTTPTransport(serverURL, token)

	ident, err := registration.Enroll(ctx, serverURL, token)
	if err != nil {
		log.Fatalf("Failed to initialize agent identity: %v", err)
	}

	agentRuntime := runtime.NewRuntime(ident)
	agentRuntime.Transport = httpTransport

	if err := agentRuntime.Start(ctx); err != nil {
		log.Fatalf("Runtime error: %v", err)
	}

	log.Printf("[JOCKY Agent] Ready and listening for JOCKY execution plans.")

	// For test / interactive execution: if run with --one-shot or just started, exit cleanly if needed or wait on signal
	if len(os.Args) > 1 && os.Args[1] == "--one-shot" {
		log.Println("[JOCKY Agent] One-shot check completed successfully.")
		return
	}

	select {
	case sig := <-sigChan:
		log.Printf("[JOCKY Agent] Received signal %v, shutting down...", sig)
	case <-ctx.Done():
		log.Println("[JOCKY Agent] Context terminated.")
	}
}
