param(
    [string]$FolderPath = "..\api\models",
    [string]$OutputFile = "models.py"
)

Get-ChildItem -Path $FolderPath -File |
    Get-Content |
    Set-Content -Path (Join-Path $FolderPath $OutputFile)