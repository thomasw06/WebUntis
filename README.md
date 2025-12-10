# WebUntis Sync — Quick Start & Troubleshooting

This project fetches your WebUntis timetable and publishes an iCalendar file (calendar.ics) via GitHub Pages. The calendar entries remain in the language your WebUntis is configured with.

If you want to use this, you only need to fork the repo and follow these steps:

1. Fork this repository

- Click "Fork" in the top-right of this repository. This creates a copy under your GitHub account.

2. Add your WebUntis credentials as GitHub Secrets (they are never saved nor shown to other users)

- Go to your fork → Settings → Secrets and variables → Actions → New repository secret.
- Add these secrets (exact names required):
  - `WEBUNTIS_SERVER` — your WebUntis host (example: `school.webuntis.com`)
  - `WEBUNTIS_SCHOOL` — school identifier used in WebUntis URL
  - `WEBUNTIS_USERNAME` — your WebUntis username
  - `WEBUNTIS_PASSWORD` — your WebUntis password
  - `WEBUNTIS_CLASS_ID` — optional: the class entityId from your WebUntis URL (example: `1234`), if you want to fetch a class timetable instead of a personal one
- Note: keep these secrets private. Do NOT commit passwords into the repository.

3. Allow the workflow to update the repository

- Go to your fork → Settings → Actions → General → Workflow permissions.
- Select **Read and write** for workflow permissions. This allows the automatic job to commit the calendar file back to your repo.

4. Enable GitHub Pages for the fork

- Go to your fork → Settings → Pages.
- Source: Branch `main`, Folder `/docs`.
- Save. GitHub Pages will publish `output/` contents and make `calendar.ics` accessible.

5. Run the workflow (first run)

- Go to your fork → Actions → Sync WebUntis Calendar.
- Click **Run workflow**, choose `main` and confirm.
- Wait for the workflow to finish. It should:
  - Run the Python script and generate `output/calendar.ics`
  - Commit and push `output/calendar.ics` into your fork so it can be fetched by your calendar client.
  - GitHub Pages will serve the file

Where to find your calendar after a successful run

- Calendar URL:
  `https://<your-github-username>.github.io/<repo-name>/calendar.ics`
- Use that URL in your calendar client (Add calendar → From Internet). If the URL returns 404 in the browser, your client cannot subscribe.

Step-by-step guide (summary)

1. Fork the repo.
2. Add Secrets: Settings → Secrets and variables → Actions → New repository secret:
   - `WEBUNTIS_SERVER`, `WEBUNTIS_SCHOOL`, `WEBUNTIS_USERNAME`, `WEBUNTIS_PASSWORD`, optional `WEBUNTIS_CLASS_ID`.
3. Allow workflow to push: Settings → Actions → General → Workflow permissions → **Read and write** → Save.
4. Enable Pages: Settings → Pages → Branch `main`, Folder `/docs` → Save.
5. Actions → Sync WebUntis Calendar → Run workflow. Wait for success.
6. Visit the Pages URL or open `https://<your-github-username>.github.io/<repo-name>/calendar.ics` and paste into Outlook/Google Calendar.

If you still see 404 after these steps:

- Open Actions → open the latest run → and the error should point exactly to the issue.
- Everyone forks and must add their own secrets. Secrets are not copied during fork.
- If you want, you can manually commit a `output/calendar.ics` file into the fork (via the GitHub web UI) as a quick fallback to have a URL that works immediately.