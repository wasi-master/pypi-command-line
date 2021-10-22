Remove-Item dist/*
$NewVersion = Read-Host -Prompt 'Enter the new version'
$Comment = Read-Host -Prompt 'Enter a comment for the new release'
(Get-Content .\pypi_cli\__init__.py) -replace '__version__\s+=\s+"(.+)"', ('__version__ = "{0}"' -f $NewVersion)  | Set-Content .\pypi_cli\__init__.py
python -m build
twine upload dist/* -p $env:TWINE_PASSWORD -u $env:TWINE_USERNAME -c $Comment -r pypi