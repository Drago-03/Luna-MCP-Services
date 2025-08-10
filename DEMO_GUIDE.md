# Demo Guide (Flattened Root)

## Connect
/mcp connect https://<ngrok>.ngrok-free.app/mcp <AUTH_TOKEN>

## Calls
/mcp call code_gen {"prompt":"Write hello world in Rust"}
/mcp call git_clone {"url":"https://github.com/tensorflow/tensorflow"}
/mcp call img_bw {"image_url":"https://picsum.photos/300"}

## Expected
Each returns JSON-RPC with a "result" field rapidly (<5s).
