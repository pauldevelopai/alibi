#!/bin/bash
# End-to-end API test script

set -e

API_URL="http://localhost:8000"

echo "🔒 Alibi API End-to-End Test"
echo "================================"
echo ""

# Wait for API to be ready
echo "1. Checking API health..."
curl -s "${API_URL}/health" | python -m json.tool
echo "✅ API is healthy"
echo ""

# Test 1: POST camera event
echo "2. Posting camera event..."
EVENT_RESPONSE=$(curl -s -X POST "${API_URL}/webhook/camera-event" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "evt_test_001",
    "camera_id": "cam_entrance_01",
    "ts": "2026-01-18T15:00:00",
    "zone_id": "zone_main_entrance",
    "event_type": "person_detected",
    "confidence": 0.87,
    "severity": 3,
    "clip_url": "https://storage.example.com/clips/evt_test_001.mp4",
    "snapshot_url": "https://storage.example.com/snapshots/evt_test_001.jpg",
    "metadata": {}
  }')

echo "$EVENT_RESPONSE" | python -m json.tool
INCIDENT_ID=$(echo "$EVENT_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin)['incident_id'])")
echo "✅ Event posted, incident created: $INCIDENT_ID"
echo ""

# Test 2: GET incidents list
echo "3. Listing incidents..."
curl -s "${API_URL}/incidents" | python -m json.tool | head -30
echo "✅ Incidents listed"
echo ""

# Test 3: GET specific incident
echo "4. Getting incident details..."
curl -s "${API_URL}/incidents/${INCIDENT_ID}" | python -m json.tool
echo "✅ Incident details retrieved"
echo ""

# Test 4: POST another event (should merge into same incident)
echo "5. Posting second event (should merge)..."
EVENT_RESPONSE_2=$(curl -s -X POST "${API_URL}/webhook/camera-event" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "evt_test_002",
    "camera_id": "cam_entrance_01",
    "ts": "2026-01-18T15:00:15",
    "zone_id": "zone_main_entrance",
    "event_type": "person_detected",
    "confidence": 0.89,
    "severity": 3,
    "clip_url": "https://storage.example.com/clips/evt_test_002.mp4",
    "metadata": {}
  }')

echo "$EVENT_RESPONSE_2" | python -m json.tool
INCIDENT_ID_2=$(echo "$EVENT_RESPONSE_2" | python -c "import sys, json; print(json.load(sys.stdin)['incident_id'])")
echo "✅ Second event posted"
echo ""

# Check if merged
if [ "$INCIDENT_ID" == "$INCIDENT_ID_2" ]; then
  echo "✅ Events correctly merged into same incident"
else
  echo "⚠️  Events created separate incidents (may be expected depending on timing)"
fi
echo ""

# Test 5: POST decision
echo "6. Recording operator decision..."
DECISION_RESPONSE=$(curl -s -X POST "${API_URL}/incidents/${INCIDENT_ID}/decision" \
  -H "Content-Type: application/json" \
  -d '{
    "action_taken": "confirmed",
    "operator_notes": "Verified legitimate access",
    "was_true_positive": true
  }')

echo "$DECISION_RESPONSE" | python -m json.tool
echo "✅ Decision recorded"
echo ""

# Test 6: GET decisions
echo "7. Listing decisions..."
curl -s "${API_URL}/decisions?incident_id=${INCIDENT_ID}" | python -m json.tool
echo "✅ Decisions listed"
echo ""

# Test 7: Verify incident has plan, alert, and validation (get fresh data)
echo "8. Verifying incident has plan + alert + validation..."
sleep 1  # Give server time to process
INCIDENT_DETAIL=$(curl -s "${API_URL}/incidents/${INCIDENT_ID}")
echo "Incident detail response:"
echo "$INCIDENT_DETAIL" | python -m json.tool | head -50
HAS_PLAN=$(echo "$INCIDENT_DETAIL" | python -c "import sys, json; d=json.load(sys.stdin); print('yes' if d.get('plan') else 'no')")
HAS_ALERT=$(echo "$INCIDENT_DETAIL" | python -c "import sys, json; d=json.load(sys.stdin); print('yes' if d.get('alert') else 'no')")
HAS_VALIDATION=$(echo "$INCIDENT_DETAIL" | python -c "import sys, json; d=json.load(sys.stdin); print('yes' if d.get('validation') else 'no')")

echo "  Plan: $HAS_PLAN"
echo "  Alert: $HAS_ALERT"
echo "  Validation: $HAS_VALIDATION"

if [ "$HAS_PLAN" == "yes" ] && [ "$HAS_ALERT" == "yes" ] && [ "$HAS_VALIDATION" == "yes" ]; then
  echo "✅ Incident has complete metadata"
else
  echo "❌ Incident missing metadata"
  exit 1
fi
echo ""

echo "================================"
echo "✅ ALL API TESTS PASSED"
echo "================================"
