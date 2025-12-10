#!/bin/bash
# cURL examples for testing async workflow execution

echo "=============================================="
echo "ASYNC WORKFLOW EXECUTION - cURL EXAMPLES"
echo "=============================================="
echo

# Get available graphs
echo "1. Getting available graphs..."
GRAPH_RESPONSE=$(curl -s http://localhost:8000/graphs)
echo "Response: $GRAPH_RESPONSE"

# Extract graph_id (assuming jq is available, fallback to basic parsing)
if command -v jq &> /dev/null; then
    GRAPH_ID=$(echo $GRAPH_RESPONSE | jq -r '.graphs[0].graph_id')
else
    # Basic parsing without jq
    GRAPH_ID=$(echo $GRAPH_RESPONSE | grep -o '"graph_id":"[^"]*' | head -1 | cut -d'"' -f4)
fi

echo "Graph ID: $GRAPH_ID"
echo

# Start async workflow
echo "2. Starting async workflow..."
ASYNC_RESPONSE=$(curl -s -X POST http://localhost:8000/run_async \
  -H "Content-Type: application/json" \
  -d "{
    \"graph_id\": \"$GRAPH_ID\",
    \"input_data\": {
      \"text\": \"Artificial intelligence transforms industries through machine learning, neural networks, and natural language processing, enabling automation in healthcare, finance, and robotics while raising privacy and bias concerns.\",
      \"max_length\": 120,
      \"chunk_size\": 80,
      \"max_refinement_iterations\": 2
    }
  }")

echo "Response: $ASYNC_RESPONSE"

# Extract run_id
if command -v jq &> /dev/null; then
    RUN_ID=$(echo $ASYNC_RESPONSE | jq -r '.run_id')
else
    RUN_ID=$(echo $ASYNC_RESPONSE | grep -o '"run_id":"[^"]*' | cut -d'"' -f4)
fi

echo "Run ID: $RUN_ID"
echo

# Monitor status
echo "3. Monitoring execution status..."
for i in {1..15}; do
    echo "Check $i:"
    STATUS_RESPONSE=$(curl -s http://localhost:8000/run_status/$RUN_ID)
    echo "  $STATUS_RESPONSE"
    
    # Check if completed or failed
    if echo $STATUS_RESPONSE | grep -q '"status":"completed"'; then
        echo "  ✅ Workflow completed!"
        break
    elif echo $STATUS_RESPONSE | grep -q '"status":"failed"'; then
        echo "  ❌ Workflow failed!"
        break
    fi
    
    sleep 1
done

echo
echo "=============================================="
echo "WEBSOCKET CONNECTION EXAMPLE"
echo "=============================================="
echo
echo "To connect to WebSocket for live streaming:"
echo "  wscat -c ws://localhost:8000/ws/run/$GRAPH_ID"
echo
echo "Or use the Python WebSocket client:"
echo "  python test_websocket_client.py"
echo
echo "WebSocket Events:"
echo "  - NODE_EXECUTED: Real-time node execution"
echo "  - COMPLETED: Workflow finished"
echo "  - ERROR: Execution failed"
echo

echo "=============================================="
echo "MANUAL TESTING COMMANDS"
echo "=============================================="
echo
echo "# 1. Start async workflow"
echo "curl -X POST http://localhost:8000/run_async \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{"
echo "    \"graph_id\": \"$GRAPH_ID\","
echo "    \"input_data\": {"
echo "      \"text\": \"Your text here...\","
echo "      \"max_length\": 100,"
echo "      \"chunk_size\": 50"
echo "    }"
echo "  }'"
echo
echo "# 2. Check status (replace RUN_ID)"
echo "curl http://localhost:8000/run_status/RUN_ID"
echo
echo "# 3. Connect to WebSocket"
echo "wscat -c ws://localhost:8000/ws/run/$GRAPH_ID"
echo