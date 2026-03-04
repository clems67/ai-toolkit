do {
    $gpuAnswer = Read-Host "Do you have an NVIDIA GPU on this machine? (yes/no)"
    $gpuAnswer = $gpuAnswer.ToLower()
} while ($gpuAnswer -notin @("yes","y","no","n"))

$packages = @("yt-dlp.FFmpeg")

foreach ($pkg in $packages) {
    winget install --id $pkg -e --source winget `
        --accept-package-agreements `
        --accept-source-agreements
}

$uvExists = Get-Command uv -ErrorAction SilentlyContinue

if (-not $uvExists) {
    winget install --id AstralSh.uv -e --source winget `
        --accept-package-agreements `
        --accept-source-agreements

    Write-Output "Restarting PowerShell session and run uv sync"

    pwsh -NoProfile -Command "uv sync"
    exit
}
else {
    Write-Output "uv already installed"
}

Write-Output "Running uv sync"
uv sync

if ($gpuAnswer -in @("yes","y")) {
    Write-Output "Installing CUDA PyTorch (GPU support)..."
    uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu130 --upgrade
} else {
    Write-Output "Installing CPU-only PyTorch..."
    uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu --upgrade
}

Write-Output ""
Write-Output "Bootstrap complete."