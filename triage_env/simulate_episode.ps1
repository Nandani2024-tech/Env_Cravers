
# Step 0: Reset the environment
$resetResponse = Invoke-WebRequest -UseBasicParsing `
    -Uri "http://localhost:8000/reset" `
    -Method POST `
    -Body '{"task_id":"task_1"}' `
    -ContentType "application/json"

$resetJson = $resetResponse.Content | ConvertFrom-Json
$patients = $resetJson.patients

Write-Host "Environment reset successful. Number of patients:" $patients.Count
Write-Host "Patient IDs:" ($patients | ForEach-Object { $_.patient_id })

# Step 1: Loop through all patients and classify them
foreach ($patient in $patients) {
    $patient_id = $patient.patient_id
    # For demonstration, we pick a dummy value (e.g., 3)
    $stepBody = @{
        task_id = "task_1"
        action_type = "classify"
        patient_id = $patient_id
        value = 3
    } | ConvertTo-Json

    $stepResponse = Invoke-WebRequest -UseBasicParsing `
        -Uri "http://localhost:8000/step" `
        -Method POST `
        -Body $stepBody `
        -ContentType "application/json"

    $stepJson = $stepResponse.Content | ConvertFrom-Json
    Write-Host "`n[STEP]" "Patient:" $patient_id
    Write-Host "Reward:" $stepJson.reward
    Write-Host "Reward Breakdown:" ($stepJson.info.reward_breakdown | ConvertTo-Json -Compress)
}

# Step 2: Fetch final score with breakdown
$scoreResponse = Invoke-WebRequest -UseBasicParsing `
    -Uri "http://localhost:8000/score" `
    -Method GET

$scoreJson = $scoreResponse.Content | ConvertFrom-Json
Write-Host "`n[FINAL SCORE]"
Write-Host ($scoreJson | ConvertTo-Json -Depth 5)
