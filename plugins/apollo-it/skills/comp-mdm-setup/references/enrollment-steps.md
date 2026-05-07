# MDM Enrollment — Detailed Steps

## 🍎 macOS — Iru (formerly Kandji)

Apollo uses **Iru** (previously known as Kandji) to manage MacBooks.

### Step 1 — Download the enrollment profile

1. Go to **[apollo.iru.com/enroll](https://apollo.iru.com/enroll)**
1. Enter the enrollment code from the **MDM Enrollment** section of the IT AI Agent Reference page
1. Click **"Download Kandji"** — this downloads a file called `kandji-enroll.mobileconfig`

### Step 2 — Open the profile

1. Go to your **Downloads folder** and open the `kandji-enroll.mobileconfig` file
1. A notification will appear saying a profile was downloaded

> ⚠️ **Do NOT click the notification** — it won't open System Settings for you.
> You need to go there manually in the next step.

### Step 3 — Install the profile in System Settings

Navigate to System Settings based on your macOS version:

- **macOS 15 or later:** System Settings → General → **Device Management**
- **macOS 13–14:** System Settings → Privacy & Security → **Profiles**
- **macOS 12 (Monterey):** System Preferences → **Profiles** (appears as a top-level item)

Once there, click **Install** and enter your device password when prompted.

> ⏳ It may take a moment to load all profiles depending on your internet connection.

### Step 4 — Confirm enrollment

You'll know it worked when:

- You see multiple profiles listed in Device Management / Profiles
- The **Iru/Kandji logo** appears in your Mac menu bar at the top of the screen

### Step 5 — Restart your Mac

Once you see the Kandji icon in the menu bar, **restart your Mac** to complete enrollment. If FileVault isn't already enabled on your device, Iru may prompt you to enable disk encryption after restart — follow the on-screen steps if so.

______________________________________________________________________

🎉 **That's it! You're enrolled.**

______________________________________________________________________

## 🪟 Windows — JumpCloud

Apollo uses **JumpCloud** to manage Windows laptops.

### Step 1 — Check your email

Look for a **Welcome email from JumpCloud** in your `@apollo.io` inbox.
If you don't see it, check your spam folder or ping `#it-help-desk`.

### Step 2 — Set up your JumpCloud account

1. Click **"Set Up Account"** in the welcome email
1. Create a strong password for your account
1. Click **Register** to complete setup

> ⚠️ **Important:** The password you set here will also be your **Windows laptop login password**. Choose it carefully.

### Step 3 — Log in to the JumpCloud portal

1. Open your browser and go to **[console.jumpcloud.com](https://console.jumpcloud.com)**
1. Log in with your `@apollo.io` email and the password you just created

### Step 4 — Start MDM enrollment

1. In the left sidebar, click **Security**
1. Navigate to **JumpCloud Device Enrollment**
1. Select **Windows** as your operating system (it's the default)
1. Click **"Start MDM Enrollment"**

### Step 5 — Complete the enrollment

1. A popup will appear — click **Open**
1. Your email and the MDM server address will be pre-filled automatically
1. Click **Next**
1. Click **"Got It"** — JumpCloud will run in the background from now on ✅

______________________________________________________________________

🎉 **That's it! You're enrolled.**
