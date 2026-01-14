# PowerShell script to update all URL name references from booking_* to reservation_*
# This maintains backend compatibility while updating user-facing URLs

$mappings = @{
    "{% url 'new_booking'" = "{% url 'new_reservation'"
    "{% url 'booking_detail'" = "{% url 'reservation_detail'"
    "{% url 'booking_confirmation'" = "{% url 'reservation_confirmation'"
    "{% url 'update_booking'" = "{% url 'update_reservation'"
    "{% url 'cancel_booking'" = "{% url 'cancel_reservation'"
    "{% url 'booking_actions'" = "{% url 'reservation_actions'"
    "{% url 'past_confirmed_trips'" = "{% url 'past_confirmed_reservations'"
    "{% url 'past_pending_trips'" = "{% url 'past_pending_reservations'"
    "{% url 'booking_activity'" = "{% url 'reservation_activity'"
    "{% url 'rebook_booking'" = "{% url 'rebook_reservation'"
    "{% url 'delete_booking'" = "{% url 'delete_reservation'"
    "{% url 'view_user_booking'" = "{% url 'view_user_reservation'"
    "{% url 'confirm_trip_action'" = "{% url 'confirm_reservation_action'"
}

# Get all template files
$templateFiles = Get-ChildItem -Path "templates" -Filter "*.html" -Recurse

Write-Host "Updating URL references in $($templateFiles.Count) template files..." -ForegroundColor Cyan
$totalReplacements = 0

foreach ($file in $templateFiles) {
    $content = Get-Content $file.FullName -Raw -Encoding UTF8
    $originalContent = $content
    $fileReplacements = 0
    
    foreach ($key in $mappings.Keys) {
        $oldValue = $key
        $newValue = $mappings[$key]
        
        if ($content -match [regex]::Escape($oldValue)) {
            $count = ([regex]::Matches($content, [regex]::Escape($oldValue))).Count
            $content = $content -replace [regex]::Escape($oldValue), $newValue
            $fileReplacements += $count
        }
    }
    
    if ($content -ne $originalContent) {
        Set-Content -Path $file.FullName -Value $content -Encoding UTF8 -NoNewline
        Write-Host "  [OK] $($file.Name): $fileReplacements replacements" -ForegroundColor Green
        $totalReplacements += $fileReplacements
    }
}

Write-Host ""
Write-Host "Complete! Total replacements: $totalReplacements" -ForegroundColor Green
