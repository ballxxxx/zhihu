# CloudBase 云托管部署脚本(PowerShell 版)
# 用法: powershell -ExecutionPolicy Bypass -File scripts\deploy_cloudbase.ps1 -EnvId <环境ID>
# 密钥从本地文件读取,不在输出中回显。
param([Parameter(Mandatory=$true)][string]$EnvId)

$ErrorActionPreference = "Stop"
$root = "D:\claude code projects\final-mate"

Set-Location $root
Write-Host "部署到 CloudBase 环境 $EnvId (构建镜像约需几分钟,请耐心等待)..."
Write-Host "密钥不随部署下发,构建完成后请在控制台配置环境变量(见说明)"

# 不带 --env-params:含内嵌引号的参数会被 PS 5.1 搅乱整条命令行
& tcb cloudrun deploy -e $EnvId -s finalmate --source $root --port 8000 --min-num 0 --max-num 2 --open-access-types "OA,PUBLIC" --force --wait
if ($LASTEXITCODE -ne 0) { Write-Host "部署命令退出码: $LASTEXITCODE"; exit $LASTEXITCODE }
Write-Host "部署完成!"
