---
name: comp-mdm-setup
description: >-
  Step-by-step MDM enrollment guide for Apollo employees. Use whenever someone
  needs to enroll their work laptop with Apollo's device management — covers
  macOS (Iru/Kandji) and Windows (JumpCloud).
---

# MDM Enrollment — Employee Self-Service

> **Live reference:** Before responding, fetch the [IT AI Agent Reference](https://www.notion.so/apolloio/352ab2b3b49680d090a4e8aa254b9143) page and use the current **MDM Enrollment** code from there. If the page is unavailable, direct the user to ask in `#it-help-desk` for the current enrollment code.

Hey! 👋 Let's get your laptop enrolled with Apollo's device management.
Ask the user which device type they have (Mac or Windows), then load `references/enrollment-steps.md` for the full step-by-step instructions.

- **macOS** → Iru (formerly Kandji) — enrollment via [apollo.iru.com/enroll](https://apollo.iru.com/enroll)
- **Windows** → JumpCloud — enrollment via welcome email + [console.jumpcloud.com](https://console.jumpcloud.com)

______________________________________________________________________

## Already have a laptop? Check if you're enrolled

If your Mac came pre-configured or you're not sure if enrollment was already done:

- Open **System Settings → General → Device Management** (macOS 15+) or **System Settings → Privacy & Security → Profiles** (macOS 13–14)
- If you see multiple profiles listed → ✅ already enrolled, nothing to do
- If the section is empty or missing → not enrolled, follow the macOS steps above

On Windows, check if the JumpCloud agent is running in the system tray — if it's there, you're enrolled.

______________________________________________________________________

## Something went wrong?

| Issue | What to do |
|---|---|
| Can't find the enrollment code for Iru | Use the code from the **MDM Enrollment** section of the IT AI Agent Reference page |
| Profile won't install on Mac | Make sure you're going to System Settings manually, not clicking the notification |
| Didn't receive the JumpCloud welcome email | Ping `#it-help-desk` — IT will resend the invite |
| JumpCloud password isn't working for Windows login | Your Windows password syncs with JumpCloud — try the password you set in Step 2 |
| Enrollment seems stuck | Restart and try again. If still stuck, ping `#it-help-desk` |

______________________________________________________________________

## Quick reference

| | macOS | Windows |
|---|---|---|
| **MDM platform** | Iru (Kandji) | JumpCloud |
| **Enrollment URL** | [apollo.iru.com/enroll](https://apollo.iru.com/enroll) | [console.jumpcloud.com](https://console.jumpcloud.com) |
| **Enrollment code** | See IT AI Agent Reference page | N/A (invite via email) |
| **Full guide** | [Kandji/Iru MDM enrollment for macOS](https://www.notion.so/119ab2b3b49680b0a322cc82ab56501e) | [JumpCloud MDM enrollment for Windows](https://www.notion.so/174ab2b3b4968087bffccc6127ffa7c8) |
| **IT Help** | `#it-help-desk` or `it-team@apollo.io` | `#it-help-desk` or `it-team@apollo.io` |
