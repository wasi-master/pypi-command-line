$InitFilePath = ".\pypi_cli\__init__.py"
$CurrentVersion = (Select-String -Path $InitFilePath -Pattern '__version__\s+=\s+"(.+)"').Matches[0].Groups[1].Value
Write-Host "Current Version: $CurrentVersion" -ForegroundColor Blue
$NewVersion = Read-Host -Prompt 'Enter the new version'
$Comment = Read-Host -Prompt 'Enter a comment for the new release'
Write-Host ""
Write-Host "Removing previous distributions" -ForegroundColor Green
Remove-Item dist/*
Remove-Item pypi_command_line.egg-info -Recurse
Write-Host "Changing version number" -ForegroundColor Green
(Get-Content $InitFilePath) -Replace '__version__\s+=\s+"(.+)"', ('__version__ = "{0}"' -f $NewVersion)  | Set-Content $InitFilePath
Write-Host "Buliding Wheel" -ForegroundColor Green
python setup.py bdist_wheel
Write-Host "Buliding Source Distribution" -ForegroundColor Green
python setup.py sdist
Write-Host "Uploading Package" -ForegroundColor Green
python -m twine upload dist/* -p $env:TWINE_PASSWORD -u $env:TWINE_USERNAME -c $Comment -r pypi