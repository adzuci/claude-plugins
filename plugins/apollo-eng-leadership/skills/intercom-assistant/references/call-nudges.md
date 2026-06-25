# Call Nudges

Use this reference when the customer is stuck, confused, blocked, or when screen sharing would resolve ambiguity faster than another text reply.

This is the single source of truth for when to offer a call. `SKILL.md` and `wave2-patterns.md` (`intro`) point here; keep the stance consistent across all three.

## The Call-Offer Rule

- Offering a call in the first human reply is the **default** for genuine troubleshooting, onboarding, a frustrated customer, or a thread already 3 or more turns deep. It correlates with higher acceptance and lower time-gaps. Because Fin handles self-serve first, a conversation that reached a human has often already cleared that bar.
- Do not offer a call by default for every reply. **Skip the offer only when ALL of these hold:**
  1. The answer is a single fact or how-to with no account state to inspect.
  1. There are zero failed troubleshooting steps in the thread.
  1. The thread is fewer than 3 back-and-forth turns.
  1. The customer has stated no urgency, frustration, or deadline.
- "Customer prefers text" only counts as a skip reason if the customer states it **after** a call was offered. Never use it to avoid offering in the first place.
- If any troubleshooting step, unclear UI state, blocked workflow, or stated deadline is present, the default is to offer.
- Keep the nudge specific and operational. Tell the customer exactly what to click and what to enable.
- A pending call request does not stop the first-response-time clock. If the customer is still waiting on us, keep the thread moving while the call is pending.

## Direct Call Request

```text
Got it. I'm going to send over the call request now. Click on the Answer Call button. Once the call starts, please enable your mic and share your screen so we can talk through things together.
```

## Softer Offer

```text
I can keep walking through this here, but a quick call may be faster since I need to see the exact screen state. If that works for you, I can send the call request now.
```

## After One Failed Step

```text
Thanks for checking that. Since the expected option still is not showing, the fastest path is for us to look at it together. I'll send the call request now; once you join, please enable your mic and share your screen.
```

## When The Customer Is Busy

```text
If now is not a good time for a call, I can keep troubleshooting here. If you do have a few minutes, a screen share should let us narrow this down much faster.
```

## If The Call Is Not Needed Yet

```text
Let's check one more thing here first. If that does not explain it, I will suggest a quick call so we can look at the screen together.
```

## Re-Trigger (8-Minute Mark)

If no call has been accepted after about 8 minutes of active chat troubleshooting, re-offer the call. Looping in text past this point usually costs more time than a short screen share.

## Timing And Reassignment

- Wait until the customer has finished typing before sending the call-offer macro, so the offer does not collide with their message.
- Re-offer on every transfer or pickup. A prior rep's offer does not carry over; the customer may not have seen it.

## Phrases To Avoid

- Do not hedge the offer away: avoid "if you prefer to keep this in chat that's fine" and "if at any point it feels easier, just let me know."
- Do not offer a call and then immediately answer the question anyway in the same message. That trains the customer to ignore the offer.

## Informed Silence

Never go silent to research mid-conversation. Say what you are doing:

```text
Let me pull this up, give me just a moment.
```

## Closing After A Call

- Resolve or close the conversation immediately after the post-call admin is done. Aim for the under-6-minute time-gap target between call end and close.
- Do not pick up new, unrelated items in the open chat unless the customer asked for a recap. Start a fresh conversation for a new issue.
- See `recap-recipe.md` for the post-call wrap-up.

## IKB Call-Offer Copy

Canonical phrasings from the IKB escalation guidance. Prefer these where they overlap with the scripts above.

Standard call offer:

```text
Would you be up for a quick call with me? You can turn on your mic and share your screen so we can look at this together.
```

Screen-share variant:

```text
The fastest way to sort this is a quick screen share. If you can join a call and share your screen, I can see the exact state and guide you live.
```

Softer mid-review transition:

```text
While I review this, would a short call be easier? We can walk through it together instead of going back and forth here.
```

Post-acceptance:

```text
Thank you. I'm going to send over the call request now. Select the Answer Call button, then enable your mic and share your screen so we can talk through things together.
```

Decline:

```text
No worries. We can continue on chat.
```

No-response check-in:

```text
Just checking back in. If a quick call works, I can send the request now. If you would rather stay on chat, that is fine too and we can keep going here.
```
