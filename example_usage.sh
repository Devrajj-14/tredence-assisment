#!/bin/bash
# Example usage of the AI Workflow Engine

echo "=========================================="
echo "AI Workflow Engine - Quick Start Guide"
echo "=========================================="
echo ""

# 1. Check server health
echo "1. Checking server health..."
curl -s http://localhost:8000/ | python -m json.tool
echo ""

# 2. List available graphs
echo "2. Getting available graphs..."
GRAPH_ID=$(curl -s http://localhost:8000/graphs | python -c "import sys, json; print(json.load(sys.stdin)['graphs'][0]['graph_id'])")
echo "Graph ID: $GRAPH_ID"
echo ""

# 3. Run the workflow
echo "3. Running summarization workflow..."
cat > /tmp/workflow_request.json << 'EOF'
{
  "graph_id": "GRAPH_ID_PLACEHOLDER",
  "input_data": {
    "text": "Artificial intelligence is revolutionizing technology. Machine learning enables computers to learn from data. Deep learning uses neural networks with multiple layers. Natural language processing allows machines to understand human language. Computer vision enables image analysis. These technologies are transforming healthcare, finance, and transportation. AI systems can diagnose diseases, detect fraud, and drive autonomous vehicles. However, ethical concerns about privacy and bias must be addressed.",
    "max_length": 100,
    "chunk_size": 80,
    "max_refinement_iterations": 3
  }
}
EOF

# Replace placeholder with actual graph ID
sed "s/GRAPH_ID_PLACEHOLDER/$GRAPH_ID/" /tmp/workflow_request.json > /tmp/workflow_request_final.json

RUN_RESPONSE=$(curl -s -X POST http://localhost:8000/graph/run \
  -H "Content-Type: application/json" \
  -d @/tmp/workflow_request_final.json)

RUN_ID=$(echo $RUN_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin)['run_id'])")
echo "Run ID: $RUN_ID"
echo ""

# 4. Show execution summary
echo "4. Execution Summary:"
echo $RUN_RESPONSE | python -c "
import sys, json
data = json.load(sys.stdin)
print(f\"  Total iterations: {len(data['execution_log'])}\")
print(f\"  Refinement loops: {data['final_state']['refinement_iterations']}\")
print(f\"  Final length: {data['final_state']['current_length']}\")
print(f\"  Target length: {data['final_state']['max_length']}\")
print(f\"\\n  Final Summary:\")
print(f\"  {data['final_state']['refined_summary'][:150]}...\")
"
echo ""

# 5. Retrieve state
echo "5. Retrieving execution state..."
curl -s http://localhost:8000/graph/state/$RUN_ID | python -c "
import sys, json
data = json.load(sys.stdin)
print(f\"  Run ID: {data['run_id']}\")
print(f\"  Timestamp: {data['timestamp']}\")
print(f\"  Execution steps: {len(data['execution_log'])}\")
"
echo ""

echo "=========================================="
echo "Workflow completed successfully!"
echo "=========================================="
echo ""
echo "Server is running at: http://localhost:8000"
echo "API docs available at: http://localhost:8000/docs"
