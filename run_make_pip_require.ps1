poetry export -f requirements.txt -o requirements.txt --without-hashes

if (-not (Select-String -Path requirements.txt -Pattern '^-e\s+\./libkoiki')) {
    $content = Get-Content requirements.txt
    @("-e ./libkoiki") + $content | Set-Content requirements.txt
}
