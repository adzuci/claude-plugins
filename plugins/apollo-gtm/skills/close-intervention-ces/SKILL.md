---
name: close-intervention-ces
description: Closes the user's open admin Intervention CEs in Salesforce in one pass. Invoke as /apollo-gtm:close-intervention-ces <report link>, using the link to their "[COPs] Pending CE - Grouped" report. Reads the owner from the link, shows the list, waits for a yes, then updates only CEs the user owns. Walks through one-time Salesforce CLI setup if needed.
argument-hint: "[report link]"
disable-model-invocation: true
---

# Close Out Intervention CEs

Author: Sam Jackson, GTME

Usage: `/apollo-gtm:close-intervention-ces <report link>`, where the link is the user's "[COPs] Pending CE - Grouped" report.

Audience: a GTME teammate who is NOT technical. Assume they have never opened Terminal. Be patient, warm, and plain.

## How to talk to this user

- One step at a time. Give a step, then wait for them to say it is done or paste what they see. Never dump the whole setup at once.
- No jargon. If you must use a word like "Terminal" or "command", explain it once in plain words.
- Always say exactly what they should see when a step works, and what to do if they see something else.
- Tell them early: "None of this can break anything. Setup is a one-time thing, about 10 minutes. After that, closing CEs takes a minute."
- If they paste a screenshot or text, read it carefully and tell them which step they are on. Do not assume.
- Reassure on scary-looking text. Many messages look like errors but are normal (see "Messages that look scary but are fine").
- Short and direct. Bullets. No em dashes.

## Entry points and the fast path (read this first)

This skill runs only when the user invokes it by name: `/apollo-gtm:close-intervention-ces <report link>`. The report link is the argument. Both forms below lead to the same place: find the user's open "admin" CEs, confirm, close them.

1. **The user passes the link to their report of open CEs** (the argument). Do not ask what they want. Treat their "admin" CEs as the work to do.
   - Read the owner name from the `value` in the link's `reportFilters` (for example `Samuel%20Jackson` is Samuel Jackson). Do not ask for the name. Say it back in one line so they can catch a wrong one, for example "Closing CEs owned by Samuel Jackson." The report ID in the link belongs to the shared report that every GTME uses, so any teammate's link has the same ID with their own name in the filter. Never assume the name is the skill author's.
   - If the link has no `reportFilters` (for example they copied it after filtering by hand), take the name from their email in context, or ask: "What is your name as it shows in Salesforce?" Do not guess. Then build their filtered link from the template below and continue.
   - The Salesforce query in Step 1 is what finds the real record Ids. Ask how many "admin" rows they see in the report, and check it matches the query count.
   - A screenshot, CSV or pasted rows are not the argument. If the user shares one with a request to close CEs, treat it as entry point 2 and use it only as the cross-check count.
2. **The user invokes the skill with no link.** Ask them to paste the link to their "[COPs] Pending CE - Grouped" report, or help them build it (see "Help the user set up THEIR OWN version of this report link"). Then do Step 0 and go on.

**Fast path.** Many users will already have the Salesforce CLI installed and logged in. Do not explain the CLI, Terminal or setup to them. In this order:
1. Run `sf org list`. Do this yourself if you can run commands.
2. If it shows an org with status Connected, say one line: "You are already set up. Finding your open admin CEs." Then go straight to Step 1.
3. Only if `sf` is missing, or the login is expired or absent, run the Setup walkthrough below, and only the part that is needed. Missing `sf` means Part 0 and Part 1, then Part 2. Installed but not logged in means Part 2 only.
4. Skip "How to talk to this user" hand-holding when they are clearly comfortable. Match their pace.

Keep the confirm step even on the fast path. Showing the list and getting a clear yes before changing anything is not optional.

## Why this exists

This skill is for when a GTME is working open interventions and needs to disposition them. It is NOT the usual "a call happened, so a CE was created" case.

For each intervention the GTME works, the GTME creates a Customer Engagement (CE) record by hand (object `Customer_Engagement__c`). It stays "Open" until it is filled in and Stage is set to Complete. This skill does the filling in and closing, in bulk, for the user's own records.

### The user must create the CE first (tell them this up front)

Say this before anything else:
"Before I can close anything, you need to create a CE in Salesforce for each intervention you worked. I close them for you after. Each CE must be set up exactly like this, or I will not find it:"

| Field in Salesforce | What to enter |
|---|---|
| Customer Engagement (the name field) | admin |
| Meeting Type | Intervention Email |
| Account | The account the intervention is for |
| Owner | Themselves (the default) |

Steps for the user:
1. In Salesforce, open the Customer Engagements tab and click New (or create it from the account).
2. Type `admin` in the Customer Engagement field.
3. Pick `Intervention Email` for Meeting Type.
4. Pick the account, then Save. Leave everything else empty, this skill fills it in.
5. Repeat for each intervention you worked.

What a correctly created CE looks like. After saving, it shows up in the Salesforce report "[COPs] Pending CE - Grouped" (Reports tab, filter Owner Name to the user's own name) as one row like this:

| Owner Name | Conversation Source | Customer Engagement Name | Stage | Meeting Type | Intervention Status | Intervention Types | Sentiment | Sentiment Details | Call Date / Time |
|---|---|---|---|---|---|---|---|---|---|
| (the user) | - | Admin | Open | Intervention Email | - | - | - | - | (a date and time) |

Tell the user: "If you see a row like this, with Stage Open, Meeting Type Intervention Email, and the status, types, sentiment columns empty, you did it right. That is exactly the row I will close for you."

Every CE they create adds one more row. They can count the rows to know how many to expect me to find.

Names may show as "admin", "Admin" or "Intervention admin". All are fine. Casing does not matter.

If the user has not created their CEs yet, stop here and let them. Come back to Step 1 when they say they are done. Do not create CEs for them.

The source of truth is the report "[COPs] Pending CE - Grouped". Every GTME uses it to see their open CEs. This skill clears the open CEs in it whose Customer Engagement Name says "admin".

Sam Jackson's own example (this is HIS report, filtered to HIS open CEs with "admin". Do not send it to teammates as theirs, they would see Sam's records):
- https://apolloio.lightning.force.com/lightning/r/Report/00OUz00000FfyArMAJ/view?reportFilters=%5B%7B%22value%22%3A%22Samuel%20Jackson%22%2C%22operator%22%3A%22equals%22%2C%22column%22%3A%22CUST_OWNER_NAME%22%7D%5D

### Help the user set up THEIR OWN version of this report link

Each user needs their own link: the same report, filtered to the open CEs with "admin" that THEY own. Walk them through it. Do not skip this, it is how they check my work.

1. Tell them: "That link above is Sam's. We will make yours. It is the same report, just filtered to your name."
2. Build their link by taking this template and replacing `USER%20FULL%20NAME` with their name, using `%20` for each space (Samuel Jackson becomes `Samuel%20Jackson`):
   ```
   https://apolloio.lightning.force.com/lightning/r/Report/00OUz00000FfyArMAJ/view?reportFilters=%5B%7B%22value%22%3A%22USER%20FULL%20NAME%22%2C%22operator%22%3A%22equals%22%2C%22column%22%3A%22CUST_OWNER_NAME%22%7D%5D
   ```
3. Give them the finished link and ask them to click it. It opens the report "[COPs] Pending CE - Grouped" already filtered to their own name.
4. Ask them to check it is theirs: the Owner Name at the left should be their name, not someone else's. If it shows "No results", they may have no open CEs yet (see "create the CE first" above) or the name does not match exactly how Salesforce spells it. Ask them to copy the name exactly as it shows on their Salesforce profile and try again.
5. Tell them to bookmark it: in Chrome, click the star in the address bar and click Done. Next round they open that bookmark to see their open CEs.
6. Ask: "How many rows with the name admin do you see?" Use that number to check the Step 1 query below. If the numbers differ, stop and work out why before changing anything.

If they would rather not use the link, they can open the report from the Reports tab in Salesforce, search "Pending CE", open "[COPs] Pending CE - Grouped", and filter Owner Name to themselves by hand.

The report shows only their open CEs. Rows whose name is not "admin" are real call CEs, so leave those alone.

## Hard rules

- Only update records owned by the person running this. Never another teammate's records. Never records that were not shown to and confirmed by the user.
- Never type passwords, tokens, or credentials for the user. They sign in themselves in their own browser.
- If any tool, site, or permission is blocked (including a permission prompt from Claude itself), stop and tell the user plainly what was blocked and why it was needed. Do not look for a workaround. Offer the manual fallback at the bottom.
- Show before you change. Update one record first, check it, then do the rest.

## The values set on every record

| Field | Value |
|---|---|
| Meeting_Type__c | Intervention Email |
| Expected_Outcome__c | Usage (WAU) |
| Sentiment__c | Neutral |
| Sentiment_Details__c | admin |
| Intervention_Status__c | Intervention Completion Call |
| Intervention_Types__c | Customer Training Session |
| Stage__c | Complete |

Say these in plain words before starting and ask "Are these the right values for this round?" If they want different values, use theirs, but only for fields they name.

## Step 0: Who is the user, and is setup already done?

Follow the fast path above. If setup is done, this step is just getting the user's name, then Step 1.

1. Get the user's full Salesforce name. Take it from the report link argument. If there is no link, use their email from context if available (samuel.jackson@apollo.io means "Samuel Jackson"). If unsure, ask: "What is your name as it shows in Salesforce?"
2. Check whether `sf` works. Run:
   ```bash
   sf org list
   ```
   - Table with an org and status "Connected": setup is done. Skip to Step 1.
   - "command not found": do Setup Part 1, then Part 2.
   - Installed, but no org, or status is expired: do Setup Part 2 only.
3. If you cannot run commands yourself, ask the user to open Terminal (Part 0 below) and paste the command, then paste back what they see.

## Setup (one time, about 10 minutes)

Explain this to the user in plain words before any step (a few sentences, not a lecture):

- Why the value: GTME intervention reports often have 20 or more open interventions. Closing each one means creating a CE first, which leaves a pile of open "admin" CEs that are really Intervention Emails. Editing them one by one is slow and tedious. This skill closes them all in one pass.
- What the CLI is: "CLI" stands for command line interface. It is a small free program from Salesforce with no screens or buttons. You give it a typed instruction and it does the job in Salesforce for you.
- Why we need it: Claude's built in Salesforce connection can read records but cannot change them. The CLI is what lets Claude update your CEs. It acts only as you, with your own Salesforce permissions, after you log in yourself.
- What they will do, in order: (1) open Terminal, the Mac app where typed instructions go, (2) install the CLI, (3) log in to Salesforce in their browser, (4) come back and let Claude do the closing.
- What they will not do: write code, change settings, or share a password with Claude. They paste a few lines and click a few buttons.
- After this, next time is a minute: Terminal and the CLI are already set up, so they only log in again if it has expired.

Then say: "Ready? I will go one step at a time."

### Part 0: What is Terminal and how do I open it

Terminal is a plain text window on your Mac where you paste a line and press Enter. That is all we use it for.

1. Press Cmd + Space together. A search box appears in the middle of the screen.
2. Type: Terminal
3. Press Enter. A window opens with a line ending in a `%` symbol and a blinking cursor.
4. To use it: click inside the window, paste with Cmd + V, press Enter.

Tell them: "Leave this window open. We will use it again in a minute." Wait for "I have it open".

### Part 1: Install the tool

1. Check what kind of Mac they have: click the Apple icon (top left), About This Mac. If it says "Chip: Apple M1/M2/M3/M4", it is Apple Silicon. If it says "Processor: Intel", it is Intel. Ask them to tell you which.
2. Open this page in Chrome: https://developer.salesforce.com/tools/salesforcecli
3. Find the macOS download that matches their Mac (Apple Silicon or Intel) and click it. A file ending in `.pkg` downloads.
4. Open the downloaded file (click it in the Chrome download bar, or find it in Downloads).
5. Click Continue / Install through the installer. It may ask for their Mac password. That is normal, they type it themselves.
6. When it says "installation was successful", click Close. Delete the installer if asked.
7. IMPORTANT: Quit Terminal completely (Cmd + Q) and open it again (Part 0). Skipping this is the number one reason the next step fails.
8. In the new Terminal window, paste this and press Enter:
   ```bash
   sf --version
   ```
   - GOOD: it prints something like `@salesforce/cli/2.xx.x`. Say "Perfect, it is installed."
   - First time only, it may also print a paragraph saying the tool "may collect usage information". That is normal. Ignore it. It is not an error.
   - BAD: `command not found: sf`. The install did not finish or Terminal was not restarted. Ask them to redo step 7. If still failing, redo the installer from step 3. If their IT software blocked the install, tell them to message Apollo IT and stop.

Claude should not try to download or install the tool itself. If it tried and the permission system blocked it, just walk the user through these steps.

### Part 2: Sign in to Salesforce (the "login")

This connects the tool to their Salesforce account. They sign in with their normal Apollo login in their own browser. Claude never sees a password.

1. Tell them: "Next, a Chrome tab will open. You will need to switch to it quickly, because it times out after about a minute."
2. In Terminal, paste this and press Enter:
   ```bash
   sf org login web --alias apolloio --instance-url https://apolloio.my.salesforce.com
   ```
3. Within a few seconds a new tab opens in their browser. Tell them to click over to it NOW.
4. On that tab, one of these will happen:
   - It asks them to sign in: use the normal Apollo login (Okta). Complete any prompts.
   - A page titled "Allow Access?" appears: click Allow.
   - They are already signed in to Salesforce, so it skips straight through. That is fine. Sometimes there is no Allow button at all.
5. SUCCESS looks like:
   - The tab says "Authentication Successful. You've successfully logged in. You can now close this browser tab or window."
   - Terminal says `Successfully authorized yourname@apollo.io with org ID ...`.
   Tell them to close the tab.
6. Confirm by pasting this in Terminal:
   ```bash
   sf org list
   ```
   They should see a table with alias `apolloio` and status `Connected`. Setup is done. Say "You will not need to do any of this again for a while."

### Setup: when something goes wrong

| What they see | What it means and what to do |
|---|---|
| `Error (AuthTimeoutError): The authentication session timed out` | They did not finish the browser step in time. Run the login command again and click over to the new tab right away. |
| No new tab opens | Copy the web address Terminal printed and paste it into Chrome. Or add `--browser chrome` to the end of the login command. |
| It opened in Safari or another browser they are not signed in to | Re-run the login command with `--browser chrome` on the end. |
| `command not found: sf` | Terminal needs restarting (Cmd + Q then reopen), or the install did not finish. Redo Part 1 step 7, then step 3 if still failing. |
| Something about port 1717 or "address in use" | Another Terminal window is still running the login. Close all Terminal windows, open a fresh one, try again. |
| "Not authorized", "blocked", "connected app" or an IT policy message | This is an Apollo security setting, not their mistake. Stop. Tell them to ask Apollo IT or Sales Ops for help. Do not try another route. |
| A "cannot be opened because the developer cannot be verified" message on the installer | Right-click the installer, choose Open, then Open again. |

### Messages that look scary but are fine

- The "may collect usage information, user environment, and crash reports" paragraph the first time `sf` runs. Normal. Ignore it.
- `Updating Record... Success` and `Querying Data... done`. Those are good news.

## Step 1: Find the user's open intervention CEs

Run (replace the name):
```bash
sf data query -o apolloio -q "SELECT Id, Name, Account__c, Stage__c, Meeting_Type__c, CreatedDate FROM Customer_Engagement__c WHERE Owner.Name = 'USER FULL NAME' AND Stage__c = 'Open' AND Meeting_Type__c = 'Intervention Email' ORDER BY CreatedDate DESC"
```
If `Account__c` is not a valid field, drop it and rerun. The Salesforce connector's `salesforce_query` tool can run the same query read only.

This query mirrors the "[COPs] Pending CE - Grouped" report for the user. Compare the count with the number of "admin" rows the user sees in that report. Add `AND Name LIKE '%admin%'` to the query so it only returns the "admin" ones (case does not matter). Leave out any open CE that does not say "admin", since those are real call CEs and are not part of this.

Show a simple table: Id, Name, Created date, plus how many were found and whether it matches the report. Then ask:
"These are your open intervention CEs. Do you want me to close all N of them, or only some?"

Wait for a clear yes. Exclude any records they name.

Expect the Name to look like "admin", "Admin" or "Intervention admin". If a found record has a different name, show it and ask before including it.

If zero are found, say so. The most likely cause is that the CE was not created yet, or was created with a different Meeting Type or owner. Remind them of the "create the CE first" table above and suggest checking the "[COPs] Pending CE - Grouped" report. Do not widen the search without asking.

## Step 2: Update one record first

Use the first confirmed Id:
```bash
sf data update record -o apolloio -s Customer_Engagement__c -i RECORD_ID -v "Meeting_Type__c='Intervention Email' Expected_Outcome__c='Usage (WAU)' Sentiment__c='Neutral' Sentiment_Details__c='admin' Intervention_Status__c='Intervention Completion Call' Intervention_Types__c='Customer Training Session' Stage__c='Complete'"
```
All fields go in one command, so Stage = Complete cannot trip a validation rule that needs the other fields filled in first.

Then re-query that record and confirm every field matches the table above. If it errors, show the exact error, stop, and do not touch the others.

## Step 3: Update the rest

Loop through the remaining confirmed Ids with the same command. Print success or the exact error per Id.

## Step 4: Verify and report

Re-query all updated Ids and show a table: Id, Stage__c, Sentiment__c, Intervention_Status__c, Intervention_Types__c, Expected_Outcome__c.

Report:
- How many succeeded.
- Any failures, with the exact Salesforce error text.
- A reminder that only the records they approved were changed.

Optional cleanup: they can disconnect any time with `sf org logout -o apolloio`. Next round they just log in again with Part 2.

## Manual fallback (if tools are blocked)

1. Open Salesforce, Customer Engagements tab, "My Open CEs" list view.
2. Tick the intervention CEs, click the pencil to mass edit, and set the fields from the table above.
3. Set Stage to Complete in the same save.
Then offer to re-check the records if a read connection is available.
