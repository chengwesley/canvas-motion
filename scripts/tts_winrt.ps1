param([string]$jobs, [string]$voice = 'Yating', [switch]$list)
# Windows built-in offline TTS (WinRT). jobs: JSON file [{ "id":..., "ssml":..., "out":... }]. Used by voice.py.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime
[Windows.Media.SpeechSynthesis.SpeechSynthesizer,Windows.Media.SpeechSynthesis,ContentType=WindowsRuntime] | Out-Null
[Windows.Storage.Streams.DataReader,Windows.Storage.Streams,ContentType=WindowsRuntime] | Out-Null
$all = [Windows.Media.SpeechSynthesis.SpeechSynthesizer]::AllVoices
if ($list) { $all | ForEach-Object { Write-Output "$($_.DisplayName)`t$($_.Language)`t$($_.Gender)" }; exit 0 }
$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | ? { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Await($op, [Type]$t) { $m = $asTask.MakeGenericMethod($t); $task = $m.Invoke($null, @($op)); $task.Wait(-1) | Out-Null; $task.Result }
$s = New-Object Windows.Media.SpeechSynthesis.SpeechSynthesizer
$v = $all | ? { $_.DisplayName -like "*$voice*" } | Select-Object -First 1
if (-not $v) { Write-Error "voice not found: $voice"; exit 2 }
$s.Voice = $v
$items = Get-Content $jobs -Raw -Encoding UTF8 | ConvertFrom-Json
foreach ($j in $items) {
  $st = Await ($s.SynthesizeSsmlToStreamAsync($j.ssml)) ([Windows.Media.SpeechSynthesis.SpeechSynthesisStream])
  $n = [uint32]$st.Size
  $r = New-Object Windows.Storage.Streams.DataReader($st.GetInputStreamAt(0))
  Await ($r.LoadAsync($n)) ([uint32]) | Out-Null
  $buf = New-Object byte[] $n; $r.ReadBytes($buf)
  [IO.File]::WriteAllBytes($j.out, $buf)
  Write-Output "ok $($j.id) $n"
}
