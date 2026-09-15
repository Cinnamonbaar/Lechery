# Project A - Run Game
$GodotPath = Join-Path $PSScriptRoot "tools\godot\Godot_v4.3-stable_win64.exe"
if (Test-Path $GodotPath) {
    Start-Process -FilePath $GodotPath -ArgumentList "--path `"$PSScriptRoot`""
} else {
    Write-Error "Godot executable not found at $GodotPath"
}
