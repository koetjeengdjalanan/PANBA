# Change to the directory where the script is located
Set-Location "$PSScriptRoot"
Write-Host "Changed directory to $(Get-Location)" -ForegroundColor Green

# Activate the virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "$PSScriptRoot\.venv\Scripts\Activate.ps1" -Verbose

Write-Host "Running PyInstaller..." -ForegroundColor Yellow

# Measure the time taken to run PyInstaller
$timeTaken = Measure-Command {
    pyinstaller --noconfirm --onefile --windowed `
        --icon "$PSScriptRoot\assets\favicon.ico" `
        --name "PANBA" `
        --upx-dir "$env:LOCALAPPDATA\Microsoft\WinGet\Links" `
        --clean --log-level "INFO" `
        --add-data "$PSScriptRoot\assets\favicon.ico;assets" `
        --add-data "$PSScriptRoot\assets;assets" `
        --hidden-import "customtkinter" `
        --paths "$PSScriptRoot\.venv\Lib\site-packages" `
        --version-file "$PSScriptRoot\win-vers.txt" `
        "$PSScriptRoot\app.py"
}

# Check if the build was successful
if ($LASTEXITCODE -eq 0) {
    Write-Host "PyInstaller completed successfully in $($timeTaken.TotalSeconds) second(s)." -ForegroundColor Green
    exit $LASTEXITCODE
}
else {
    Write-Host "PyInstaller failed in $($timeTaken.TotalSeconds) second(s)." -ForegroundColor Red
    exit $LASTEXITCODE
}