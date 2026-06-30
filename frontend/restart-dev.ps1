# Frontend Dev Server Restart Script
Write-Host "🔧 Restarting Frontend Dev Server..." -ForegroundColor Cyan
Write-Host ""

# Clear caches
Write-Host "Clearing caches..." -ForegroundColor Yellow
if (Test-Path "node_modules\.vite") {
    Remove-Item -Recurse -Force "node_modules\.vite"
    Write-Host "  ✓ Cleared .vite cache" -ForegroundColor Green
}
if (Test-Path ".tanstack") {
    Remove-Item -Recurse -Force ".tanstack"
    Write-Host "  ✓ Cleared .tanstack cache" -ForegroundColor Green
}

Write-Host ""
Write-Host "✅ Caches cleared!" -ForegroundColor Green
Write-Host ""
Write-Host "Now run: npm run dev" -ForegroundColor Cyan
Write-Host ""
Write-Host "Then hard refresh your browser (Ctrl+Shift+R)" -ForegroundColor Yellow
