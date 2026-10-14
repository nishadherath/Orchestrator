$ErrorActionPreference='Continue'
$taskRoot='D:/Code/Claude/Orchestrator/.graft'
$record=[ordered]@{started_at=[DateTime]::UtcNow.ToString('o');ok=$false;protection_changed=$false;seconds=20;max_trace_megabytes=512;buffer_megabytes=256;other_sessions_stopped=$false;handshake=$true}
$before=(& xperf -loggers 2>&1 | Out-String)
$before | Set-Content "$taskRoot/kernel5-before.log"
if ($before -match '(?m)^Logger Name\s*:\s*NT Kernel Logger\s*$' -or $LASTEXITCODE -ne 0) {
    $record.error='Default kernel session exists or enumeration failed; refusing to replace it.'
} else {
    & xperf -on PROC_THREAD+LOADER+DRIVERS+FILENAME+FLT_IO_INIT+FLT_IO+FLT_FASTIO+FLT_IO_FAILURE -stackwalk MiniFilterPreOpInit+MiniFilterPostOpInit -BufferSize 1024 -MinBuffers 256 -MaxBuffers 256 -FileMode Circular -MaxFile 512 -f "$taskRoot/kernel5-bounded.etl" *> "$taskRoot/kernel5-start.log"
    $record.start_exit=$LASTEXITCODE
    if ($LASTEXITCODE -eq 0) {
        Set-Content "$taskRoot/kernel5-recorder-ready" ([DateTime]::UtcNow.ToString('o'))
        $end=[DateTime]::UtcNow.AddSeconds(120)
        while (!(Test-Path "$taskRoot/kernel5-release") -and [DateTime]::UtcNow -lt $end) {Start-Sleep -Milliseconds 100}
        $record.workload_released=Test-Path "$taskRoot/kernel5-release"
        Start-Sleep -Seconds 20
        & xperf -stop *> "$taskRoot/kernel5-stop.log"
        $record.stop_exit=$LASTEXITCODE
        if ($LASTEXITCODE -eq 0) {
            & xperf -merge "$taskRoot/kernel5-bounded.etl" "$taskRoot/kernel5-merged.etl" -compress -suppresspii *> "$taskRoot/kernel5-merge.log"
            $record.merge_exit=$LASTEXITCODE;$record.ok=$LASTEXITCODE -eq 0
        }
    } else {$record.error='Owned kernel session start failed; inspect start log.'}
}
$record.ended_at=[DateTime]::UtcNow.ToString('o')
$record | ConvertTo-Json | Set-Content "$taskRoot/kernel5-recording.json" -Encoding UTF8
