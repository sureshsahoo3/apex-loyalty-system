<#
.SYNOPSIS
    Remove all Azure resources created by azure-deploy.ps1
.EXAMPLE
    .\azure-teardown.ps1
    .\azure-teardown.ps1 -ResourceGroup "my-rg"
#>
param([string]$ResourceGroup = "apex-loyalty-rg")

Write-Host "Deleting resource group '$ResourceGroup' and all resources inside it..." -ForegroundColor Yellow
az group delete --name $ResourceGroup --yes --no-wait
Write-Host "Deletion initiated (runs in background on Azure)." -ForegroundColor Green
