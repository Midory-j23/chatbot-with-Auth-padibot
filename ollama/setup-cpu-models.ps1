# Force Ollama to CPU mode on Windows and create CPU-only model aliases.
# Run in PowerShell AFTER quitting Ollama from the system tray.

Write-Host "Setting user environment variables for CPU-only Ollama..."
setx OLLAMA_GPU_LAYERS "0" | Out-Null
setx OLLAMA_VULKAN "false" | Out-Null

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Creating CPU-only models (this may take a minute)..."
ollama create qwen3-cpu -f "$root\Modelfile.qwen3-cpu"
ollama create gemma3-cpu -f "$root\Modelfile.gemma3-cpu"

Write-Host ""
Write-Host "Done. Next steps:"
Write-Host "  1. Start Ollama from the Start menu (or run: ollama serve)"
Write-Host "  2. Test:  ollama run qwen3-cpu hello"
Write-Host "  3. Restart backend: cd Backend\app ; uvicorn main:app --reload"
