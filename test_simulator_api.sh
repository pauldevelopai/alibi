#!/bin/bash

# Test script for Alibi Simulator API endpoints
# Requires: curl, jq
# Usage: ./test_simulator_api.sh

set -e

API_BASE="http://localhost:8000"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================"
echo "Alibi Simulator API Tests"
echo "============================================"
echo ""

# Test 1: Check simulator status (should be stopped initially)
echo "Test 1: Check initial simulator status"
STATUS=$(curl -s "${API_BASE}/sim/status")
echo "$STATUS" | jq .
RUNNING=$(echo "$STATUS" | jq -r '.running')
if [ "$RUNNING" = "false" ]; then
    echo -e "${GREEN}✓ Simulator initially stopped${NC}"
else
    echo -e "${RED}✗ Simulator should be stopped initially${NC}"
    exit 1
fi
echo ""

# Test 2: Start simulator
echo "Test 2: Start simulator (normal_day scenario, 30 events/min, seed 42)"
START_RESPONSE=$(curl -s -X POST "${API_BASE}/sim/start" \
    -H "Content-Type: application/json" \
    -d '{
        "scenario": "normal_day",
        "rate_per_min": 30,
        "seed": 42
    }')
echo "$START_RESPONSE" | jq .
START_STATUS=$(echo "$START_RESPONSE" | jq -r '.status')
if [ "$START_STATUS" = "started" ]; then
    echo -e "${GREEN}✓ Simulator started successfully${NC}"
else
    echo -e "${RED}✗ Failed to start simulator${NC}"
    exit 1
fi
echo ""

# Test 3: Check status while running
echo "Test 3: Check status while running"
sleep 3
STATUS=$(curl -s "${API_BASE}/sim/status")
echo "$STATUS" | jq .
RUNNING=$(echo "$STATUS" | jq -r '.running')
EVENTS=$(echo "$STATUS" | jq -r '.events_generated')
if [ "$RUNNING" = "true" ] && [ "$EVENTS" -gt 0 ]; then
    echo -e "${GREEN}✓ Simulator is running and generating events${NC}"
else
    echo -e "${RED}✗ Simulator not running properly${NC}"
    exit 1
fi
echo ""

# Test 4: Check that incidents are being created
echo "Test 4: Check that incidents are being created"
sleep 2
INCIDENTS=$(curl -s "${API_BASE}/incidents")
INCIDENT_COUNT=$(echo "$INCIDENTS" | jq '. | length')
echo "Incidents created: $INCIDENT_COUNT"
if [ "$INCIDENT_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ Incidents are being created from simulator events${NC}"
else
    echo -e "${YELLOW}⚠ No incidents created yet (may need more time)${NC}"
fi
echo ""

# Test 5: Stop simulator
echo "Test 5: Stop simulator"
STOP_RESPONSE=$(curl -s -X POST "${API_BASE}/sim/stop")
echo "$STOP_RESPONSE" | jq .
STOP_STATUS=$(echo "$STOP_RESPONSE" | jq -r '.status')
if [ "$STOP_STATUS" = "stopped" ]; then
    echo -e "${GREEN}✓ Simulator stopped successfully${NC}"
else
    echo -e "${RED}✗ Failed to stop simulator${NC}"
    exit 1
fi
echo ""

# Test 6: Verify simulator is stopped
echo "Test 6: Verify simulator is stopped"
STATUS=$(curl -s "${API_BASE}/sim/status")
RUNNING=$(echo "$STATUS" | jq -r '.running')
if [ "$RUNNING" = "false" ]; then
    echo -e "${GREEN}✓ Simulator confirmed stopped${NC}"
else
    echo -e "${RED}✗ Simulator still running${NC}"
    exit 1
fi
echo ""

# Test 7: Replay events from JSONL
echo "Test 7: Replay events from JSONL"
JSONL_DATA='{"event_id":"replay_001","camera_id":"cam_entrance_main","ts":"2026-01-18T10:00:00","zone_id":"zone_entrance","event_type":"person_detected","confidence":0.85,"severity":2,"clip_url":"https://example.com/clip1.mp4","snapshot_url":"https://example.com/snap1.jpg","metadata":{"person_count":1}}
{"event_id":"replay_002","camera_id":"cam_entrance_main","ts":"2026-01-18T10:00:30","zone_id":"zone_entrance","event_type":"loitering","confidence":0.78,"severity":3,"clip_url":"https://example.com/clip2.mp4","snapshot_url":"https://example.com/snap2.jpg","metadata":{"duration_seconds":180}}'

REPLAY_RESPONSE=$(curl -s -X POST "${API_BASE}/sim/replay" \
    -H "Content-Type: application/json" \
    -d "{\"jsonl_data\": $(echo "$JSONL_DATA" | jq -Rs .)}")
echo "$REPLAY_RESPONSE" | jq .
REPLAYED=$(echo "$REPLAY_RESPONSE" | jq -r '.events_replayed')
if [ "$REPLAYED" -eq 2 ]; then
    echo -e "${GREEN}✓ Successfully replayed 2 events${NC}"
else
    echo -e "${RED}✗ Failed to replay events correctly${NC}"
    exit 1
fi
echo ""

# Test 8: Try to start with invalid scenario
echo "Test 8: Try to start with invalid scenario (should fail)"
INVALID_RESPONSE=$(curl -s -X POST "${API_BASE}/sim/start" \
    -H "Content-Type: application/json" \
    -d '{
        "scenario": "invalid_scenario",
        "rate_per_min": 10
    }')
echo "$INVALID_RESPONSE" | jq .
if echo "$INVALID_RESPONSE" | jq -e '.detail' > /dev/null; then
    echo -e "${GREEN}✓ Correctly rejected invalid scenario${NC}"
else
    echo -e "${RED}✗ Should have rejected invalid scenario${NC}"
    exit 1
fi
echo ""

# Test 9: Try to start simulator twice (should fail)
echo "Test 9: Try to start simulator twice (should fail)"
curl -s -X POST "${API_BASE}/sim/start" \
    -H "Content-Type: application/json" \
    -d '{"scenario": "quiet_shift", "rate_per_min": 10}' > /dev/null
DOUBLE_START=$(curl -s -X POST "${API_BASE}/sim/start" \
    -H "Content-Type: application/json" \
    -d '{"scenario": "quiet_shift", "rate_per_min": 10}')
echo "$DOUBLE_START" | jq .
if echo "$DOUBLE_START" | jq -e '.detail' > /dev/null; then
    echo -e "${GREEN}✓ Correctly rejected double start${NC}"
else
    echo -e "${RED}✗ Should have rejected double start${NC}"
    exit 1
fi
# Clean up
curl -s -X POST "${API_BASE}/sim/stop" > /dev/null
echo ""

echo "============================================"
echo -e "${GREEN}✅ All simulator API tests passed!${NC}"
echo "============================================"
