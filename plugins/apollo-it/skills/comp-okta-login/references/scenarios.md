# Okta Login — Detailed Troubleshooting Scenarios

## 📱 Scenario A — MFA / Okta Verify isn't working (start here!)

This is the most common login issue at Apollo. Try these steps first:

**Push notification not arriving on your phone?**

1. Force-quit the Okta Verify app and reopen it
1. Check your phone's notification settings for Okta Verify (make sure notifications are on)
1. Instead of waiting for a push, tap **"Enter a code"** on the login screen and use the 6-digit TOTP code shown in Okta Verify

**On iOS and Slack mobile not letting you log in after a period of inactivity?**

1. Force-quit Okta Verify and reopen it
1. Try logging into Slack again — the push should arrive now
1. If not, switch to the 6-digit code option instead of the push

**Lost your phone or changed devices?**

- You won't be able to approve the MFA push without your old device
- IT needs to reset your authenticator → see **"Need IT help?"** below

______________________________________________________________________

## 🔑 Scenario B — Forgot your password / can't log in

Password resets at Apollo require IT — this isn't self-serve.

Just let me know and I'll open a ticket for you. IT will verify your identity (quick Zoom or Slack huddle) and reset it securely.

Have ready:

- Your `@apollo.io` email
- Whether you still have access to your phone for MFA (it helps IT choose the fastest path)

______________________________________________________________________

## 💻 Scenario C — MacBook locked / "Your account is locked"

If your MacBook is showing **"Your account is locked"** or refusing your password:

**Automated unlock via Iru (Kandji)**
Apollo has an automated workflow connected to our MDM (Iru/Kandji) that can unlock MacBook accounts automatically. Just ping `#it-help-desk` and mention your MacBook is locked — the IT agent will trigger the workflow. This information is recorded in `#it-help-desk` so the Glean agent can assist with quick resolution.

______________________________________________________________________

## 💻 Scenario C-alt — Windows laptop locked / "Your account is locked"

If your Windows laptop is showing **"Your account is locked"** or refusing your password:

**JumpCloud Self-Service (self-serve unlock portal)**
JumpCloud has a self-service unlock portal. Check your onboarding email or ask IT for the link — you may be able to unlock your account directly without waiting. This is the fastest way to get back in!

______________________________________________________________________

## 🔒 Scenario D — Okta account locked (too many failed attempts)

This means too many wrong password attempts triggered a lockout in Okta itself (not the Mac).

This needs IT to unlock it — it's not self-serve. Let me open a ticket for you.

Tell me:

- Your `@apollo.io` email
- Whether you also need a password reset, or just an unlock

______________________________________________________________________

## 🆕 Scenario E — New hire / first-time setup not working

If you received your welcome email but can't complete the account setup:

1. Make sure you're using the link from the **most recent** welcome email (older links expire)
1. Try opening the link in an **incognito/private** browser window
1. If it's still broken → IT needs to resend the setup link

Tell me your name, `@apollo.io` email, and start date and I'll open a ticket right away.

______________________________________________________________________

## Need IT help?

If none of the self-serve steps above worked, IT can fix it — they just need to verify your identity first (quick Zoom or Slack huddle) for anything involving passwords or authenticators.

Tell me:

1. Your `@apollo.io` email
1. Which scenario above matches your situation
1. Whether it's urgent (blocking you from working right now)

I'll open a ticket and get someone on it. 🛠️

______________________________________________________________________

## Quick links

- Okta login: **[apolloio.okta.com](https://apolloio.okta.com)**
- Okta Verify app: Available on iOS App Store and Google Play Store
- IT Help Desk tickets: **[apollopde.atlassian.net/servicedesk/customer/portal/217](https://apollopde.atlassian.net/servicedesk/customer/portal/217)**
- Slack: Ping `@it-help` in `#it-help-desk` for urgent issues
