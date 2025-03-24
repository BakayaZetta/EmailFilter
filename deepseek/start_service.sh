#!/bin/sh
#
curl -fsSL https://ollama.com/install.sh

# Start Ollama in the background
ollama serve &

# Wait for Ollama to start
sleep 5

# Pull and run <YOUR_MODEL_NAME>
ollama run deepseek:1.5b
