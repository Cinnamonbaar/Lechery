# Project A - Push to GitHub
Set-Location -LiteralPath $PSScriptRoot
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " Pushing Project A to GitHub: Cinnamonbaar/Lechery" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
git push -u origin main --force
if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[SUCCESS] Project pushed to GitHub successfully!" -ForegroundColor Green
} else {
    Write-Host "`n[NOTICE] Push exited with code $LASTEXITCODE." -ForegroundColor Yellow
}
Write-Host "`nPress any key to close this window..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
