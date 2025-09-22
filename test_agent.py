#!/usr/bin/env python3
"""
Test script to run the SignalWire agent standalone
"""

from app.services.signalwire_agent import loan_intake_agent

if __name__ == "__main__":
    print("Starting SignalWire Agent on port 8000...")
    print("Agent route: /agent/intake")
    print("Full URL: http://localhost:8000/agent/intake")
    print("Press Ctrl+C to stop")
    
    # Start the agent server
    loan_intake_agent.serve()