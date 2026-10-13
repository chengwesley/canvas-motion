param([string]$list, [string]$out, [string]$culture = 'zh-TW')
# Windows built-in offline speech recognition. list: text file of wav paths; out: JSON [{ wav, text }]. Used by voice.py
# to pick the clearest of several TTS takes (CER). Homophones are common, so CER is only a relative score.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$ci = New-Object System.Globalization.CultureInfo($culture)
$res = @()
foreach ($w in (Get-Content $list -Encoding UTF8)) {
  if (-not $w) { continue }
  $e = New-Object System.Speech.Recognition.SpeechRecognitionEngine($ci)
  $e.LoadGrammar((New-Object System.Speech.Recognition.DictationGrammar))
  $e.SetInputToWaveFile($w)
  $txt = ''
  while ($true) { try { $r = $e.Recognize() } catch { break }; if ($r -eq $null) { break }; $txt += $r.Text }
  $e.Dispose()
  $res += [pscustomobject]@{ wav = [string]$w; text = $txt }
}
[IO.File]::WriteAllText($out, (ConvertTo-Json @($res) -Depth 3), (New-Object System.Text.UTF8Encoding($false)))
