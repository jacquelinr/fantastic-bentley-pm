---
name: batch-send-emails
description: 'Batch send a user-approved email to many recipients by loading the subject and body from a separate file, then sending through Microsoft Outlook locally installed, fallback to Microsoft Graph Mail. Use when: bulk email users, send announcement to many users, send product update email, notify a user list, batch outbound email, reuse an email template file.'
argument-hint: '<recipient-source> <email-content-file>'
user-invocable: true
---

# Batch Send Emails

Batch send an email to many recipients while keeping the actual email content in a separate file.

**Author:** Jacqueline Chen

## When to Use

WHEN: bulk email users, send announcement to many users, send product update email, notify a user list, batch outbound email, reuse an email template file.

## Prerequisites

- The sender must have access to a Microsoft 365 mailbox that can send mail.
- Microsoft Graph access is available with `Mail.Send` permission for the sending identity.
- A recipient list is available as either:
  - a text or CSV file, or
  - a comma-separated list of email addresses from the user.
- The email subject and body live in a separate file.

## Email Content Source

Always load the email content from a separate file instead of embedding it directly in the command flow.

Default template reference: [email-template.md](./templates/email-template.md)

If the user provides another file path, use that file as the source of truth for the subject and body.

## Recipient List Source

Use a recipient list template when the user is supplying a CSV file.

Default template reference: [recipient-list-template.csv](./templates/recipient-list-template.csv)

Expected CSV columns:
- `first name`
- `last name`
- `email address`

If the user provides another recipient file, verify that it includes equivalent columns before sending.

## CC List Source

Use a separate CC list template when the user wants the same CC recipients applied to each outgoing email.

Default template reference: [cc-list-template.csv](./templates/cc-list-template.csv)

Expected CSV columns:
- `email address`

If the user provides a CC file, verify that it includes equivalent columns before sending.

## Workflow

### Step 1: Collect Inputs

Ask the user for:
1. The sender mailbox address
2. The recipient source
3. The optional CC source
4. The email content file path
5. Whether the body should be sent as `Text` or `HTML`

Supported recipient sources:
- Plain text file with one email address per line
- CSV file matching [recipient-list-template.csv](./templates/recipient-list-template.csv)
- Comma-separated email addresses

Supported CC sources:
- No CC list
- CSV file matching [cc-list-template.csv](./templates/cc-list-template.csv)
- Comma-separated email addresses

### Step 2: Load and Validate the Email File

Read the referenced email file before doing anything else.

Expected structure:

```md
Subject: Your subject line here

Body:
Hello {{first name}},

First paragraph.

Regards,
Product Team
```

Supported placeholders:
- `{{first name}}`
- `{{email address}}`

Personalization examples:

```md
Subject: Action needed for {{first name}}

Body:
Hello {{first name}},

We have an update for the account linked to {{email address}}.

Regards,
Product Team
```

```md
Subject: Product update for {{first name}}

Body:
Hello {{first name}},

Your registered email is {{email address}}.

Regards,
Product Team
```

Validation rules:
- A `Subject:` line must be present.
- A `Body:` section must be present.
- Stop if either section is missing.
- Preserve the body content exactly unless the user asks for edits.
- If placeholders are used, replace them per recipient from the CSV row before sending.

### Step 3: Load and Validate Recipients

Normalize recipients into a de-duplicated list.

For CSV input, read the recipient list template columns and use `email address` as the send target while preserving `first name` for personalization.

Validation rules:
- Remove blank lines.
- Trim whitespace.
- De-duplicate addresses case-insensitively.
- For CSV input, require `first name`, `last name`, and `email address` headers.
- Stop and report any invalid email addresses.

Present the final count to the user.

Before moving on, display the exact resolved recipient addresses from the execution environment that will actually be used for sending. Do not rely only on what the editor currently shows.

Example preview:

```text
RESOLVED RECIPIENTS:
  1. ada.lovelace@example.com
  2. grace.hopper@example.com
```

If the resolved list does not match the user's expectation, stop before sending and ask the user to fix or save the recipient source first.

### Step 3a: Load and Validate CC Recipients

If a CC source is provided, normalize it into a de-duplicated list.

Validation rules:
- Remove blank lines.
- Trim whitespace.
- De-duplicate addresses case-insensitively.
- Require `email address` for CSV input.
- Stop and report any invalid email addresses.

Display the exact resolved CC addresses from the execution environment before sending.

Example preview:

```text
RESOLVED CC RECIPIENTS:
  1. reviewer@example.com
  2. manager@example.com
```

### Step 4: Confirm Before Sending

Display a summary and require explicit confirmation:

```text
SUMMARY:
  Sender:      sender@contoso.com
  Recipients:  48
  CC:          2
  Content:     ./templates/email-template.md
  Format:      HTML
  Preview:     resolved recipients displayed from execution environment
  Action:      POST /users/{sender}/sendMail via Microsoft Graph

Proceed? (y/n)
```

Do not send anything without confirmation.

### Step 5: Send in Controlled Batches

Default approach: send one message per recipient so each user gets a direct email and recipient lists are not exposed.

If the email template includes placeholders such as `{{first name}}`, generate the final subject and body separately for each recipient before calling Microsoft Graph. Use first-name-only personalization for individual recipient emails.

Use Microsoft Graph:

```http
POST https://graph.microsoft.com/v1.0/users/{senderMailbox}/sendMail
Authorization: Bearer {token}
Content-Type: application/json

{
  "message": {
    "subject": "{subject}",
    "body": {
      "contentType": "Text",
      "content": "{body}"
    },
    "toRecipients": [
      {
        "emailAddress": {
          "address": "user@example.com"
        }
      }
    ],
    "ccRecipients": [
      {
        "emailAddress": {
          "address": "reviewer@example.com"
        }
      }
    ]
  },
  "saveToSentItems": true
}
```

Operational guidance:
- Process recipients in small batches, for example 25 at a time.
- Add a short pause between batches if sending a large volume.
- Record success or failure per recipient.

### Step 6: Report Results

Return a final summary:

```text
RESULTS:
  Sent:    46
  Failed:  2

  Failed recipients:
  - bad-user@example.com: HTTP 400
  - blocked-user@example.com: HTTP 403
```

## PowerShell Script Template

When the user wants a script, generate this pattern that reads the email from a separate file:

```powershell
$sender = "sender@contoso.com"
$token = "{GRAPH_BEARER_TOKEN}"
$recipientFile = ".\\templates\\recipient-list-template.csv"
$ccFile = ".\\templates\\cc-list-template.csv"
$emailFile = ".\\templates\\email-template.md"
$contentType = "Text"

$subjectLine = Select-String -Path $emailFile -Pattern '^Subject:\s*(.+)$'
if (-not $subjectLine) {
    throw "Missing Subject line in $emailFile"
}
$subject = $subjectLine.Matches[0].Groups[1].Value.Trim()

$rawEmail = Get-Content -Path $emailFile -Raw
$bodyMatch = [regex]::Match($rawEmail, 'Body:\s*(.*)$', [System.Text.RegularExpressions.RegexOptions]::Singleline)
if (-not $bodyMatch.Success) {
    throw "Missing Body section in $emailFile"
}
$bodyTemplate = $bodyMatch.Groups[1].Value.Trim()

$recipients = Import-Csv -Path $recipientFile |
  Where-Object { $_.'email address' } |
  Sort-Object -Property 'email address' -Unique

$ccRecipients = @()
if (Test-Path $ccFile) {
  $ccRecipients = Import-Csv -Path $ccFile |
    Where-Object { $_.'email address' } |
    Sort-Object -Property 'email address' -Unique
}

Write-Host "Resolved recipients from execution environment:"
$recipients | ForEach-Object {
  Write-Host " - $($_.'email address'.Trim())"
}

if ($ccRecipients.Count -gt 0) {
  Write-Host "Resolved CC recipients from execution environment:"
  $ccRecipients | ForEach-Object {
    Write-Host " - $($_.'email address'.Trim())"
  }
}

$proceed = Read-Host "Proceed with send? (y/n)"
if ($proceed -ne 'y') {
  throw 'Send cancelled before execution'
}

$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type"  = "application/json"
}

foreach ($recipient in $recipients) {
  $personalizedSubject = $subject `
    -replace '\{\{first name\}\}', $recipient.'first name' `
    -replace '\{\{email address\}\}', $recipient.'email address'

  $personalizedBody = $bodyTemplate `
    -replace '\{\{first name\}\}', $recipient.'first name' `
    -replace '\{\{email address\}\}', $recipient.'email address'

    $payload = @{
        message = @{
      subject = $personalizedSubject
            body = @{
                contentType = $contentType
        content = $personalizedBody
            }
            toRecipients = @(
                @{
                    emailAddress = @{
            address = $recipient.'email address'.Trim()
                    }
                }
            )
            ccRecipients = @(
              $ccRecipients | ForEach-Object {
                @{
                  emailAddress = @{
                    address = $_.'email address'.Trim()
                  }
                }
              }
            )
        }
        saveToSentItems = $true
    } | ConvertTo-Json -Depth 6

    try {
        Invoke-RestMethod `
            -Method Post `
            -Uri "https://graph.microsoft.com/v1.0/users/$sender/sendMail" `
            -Headers $headers `
            -Body $payload
            Write-Host "Sent to $($recipient.'email address')"
    }
    catch {
            Write-Host "Failed for $($recipient.'email address'): $($_.Exception.Message)"
    }
}
```

## Key Constraints

- The skill must read the email subject and body from a separate file.
- CSV recipient files should follow the provided recipient list template.
- CSV CC files should contain the `email address` column.
- Personalization for individual recipient emails should only use `first name` unless the user explicitly asks for more.
- Always preview the resolved recipient addresses from the execution environment before sending.
- Do not expose recipient lists to other recipients unless the user explicitly asks for BCC batching.
- Do not send without explicit user confirmation.
- Graph throttling may apply for larger recipient lists.
- Mailbox policies or tenant restrictions may block sending from shared or service mailboxes.