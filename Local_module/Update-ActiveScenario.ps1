Param(
    [string]$ScenarioDir
)

Split-Path $ScenarioDir -Leaf | Out-File .\active_scenario.txt -Encoding ascii