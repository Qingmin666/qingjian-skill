param(
 [ValidateSet('codex','claude-code')][string]$Client='codex',
 [string]$Destination=''
)
$ErrorActionPreference='Stop'
$source=Join-Path (Split-Path -Parent $PSScriptRoot) 'skills\qingjian'
if(!$Destination){
 $base=if($Client -eq 'codex'){Join-Path $env:USERPROFILE '.codex\skills'}else{Join-Path $env:USERPROFILE '.claude\skills'}
 $Destination=Join-Path $base 'qingjian'
}
$target=[IO.Path]::GetFullPath($Destination)
if((Split-Path -Leaf $target) -ne 'qingjian'){throw 'Destination must be a skill directory named qingjian'}
if(!(Test-Path -LiteralPath (Join-Path $source 'SKILL.md'))){throw 'Source skill missing'}
if(Test-Path -LiteralPath $target){throw 'Destination already exists. Preserve it and review changes before updating; nothing was overwritten.'}
New-Item -ItemType Directory -Force -Path $target | Out-Null
Get-ChildItem -LiteralPath $source -Force | ForEach-Object {Copy-Item -LiteralPath $_.FullName -Destination $target -Recurse}
Get-ChildItem -LiteralPath $source -Recurse -File | ForEach-Object {
 $relative=$_.FullName.Substring($source.Length).TrimStart('\')
 $copied=Join-Path $target $relative
 if((Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $copied -Algorithm SHA256).Hash){throw 'Copy verification failed; installation is incomplete'}
}
Write-Host ('Installed skill files: '+$target)
Write-Host 'Reload the client and invoke $qingjian. MCP connection must already be configured; this script does not change MCP configuration.'
