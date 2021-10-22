$NewVersion = Read-Host -Prompt 'Enter the new version'
$Comment = Read-Host -Prompt 'Enter a comment for the new release'
Write-Host ""
Write-Host "Removing previous distributions" -ForegroundColor Green
Remove-Item dist/*
Write-Host "Changing version number" -ForegroundColor Green
(Get-Content .\pypi_cli\__init__.py) -replace '__version__\s+=\s+"(.+)"', ('__version__ = "{0}"' -f $NewVersion)  | Set-Content .\pypi_cli\__init__.py
Write-Host "Buliding Package" -ForegroundColor Green
python -m build
Write-Host "Uploading Package" -ForegroundColor Green
twine upload dist/* -p $env:TWINE_PASSWORD -u $env:TWINE_USERNAME -c $Comment -r pypi