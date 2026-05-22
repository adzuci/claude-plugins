# Category 2 — SaaS without Personal Data (Not Product-Related)

Use this playbook when the contract is a software subscription used internally at Apollo that
does NOT access, process, or store personal data and does NOT integrate with Apollo's product.

**Redline posture: Near-zero.** This is Apollo's most permissive category. Standard SaaS
terms — even vendor-favorable ones — are acceptable. The vendor wrote this contract for a
thousand customers and it's designed to be signed. Do not redline things just because they
could theoretically be better. There are exactly two hard stops; everything else is fine.

The question to ask for each clause is not "is this ideal?" but "does this actually hurt
Apollo?" If the answer is no, leave it alone.

---

## The Two Hard Stops

These are the only provisions that require action in a Category 2 contract. Check them and
stop — if neither is present, the contract is GREEN.

### Hard Stop 1 — Vendor Claims Ownership of Apollo's Data or Output

The vendor may not claim ownership of, or a broad perpetual license to, data Apollo inputs
into the platform, configurations Apollo creates, or outputs Apollo generates using the tool.

**Acceptable:** Vendor retains ownership of its software and platform. Vendor may use
aggregated/anonymized usage data for product improvement provided Apollo's data is not
identifiable.

**Not acceptable:** Vendor claims to own what Apollo puts in or creates. This is a hard stop
regardless of the contract value — it creates an IP problem that scales with every use of the
tool.

**Redline action:** Delete the offending language and insert: "As between the parties, Apollo
retains all right, title, and interest in and to the data Apollo inputs into the platform and
any outputs Apollo generates through use of the platform."

---

### Hard Stop 2 — Vendor Provides No Indemnification to Apollo Whatsoever

The vendor must provide some form of indemnification or liability coverage to Apollo. A
contract that is entirely one-directional — Apollo indemnifies vendor but vendor has zero
obligations to Apollo — is not acceptable even for a low-risk tool.

**Acceptable:** Vendor indemnifies Apollo for third-party IP infringement claims arising from
vendor's own software. This is the minimum. Mutual indemnification is better but not required.

**Not acceptable:** Vendor expressly disclaims all indemnification obligations to Apollo, or
the indemnification section covers only Apollo's obligations to the vendor with no
corresponding vendor obligation. Apollo ends up fully exposed to vendor-caused problems with
no recourse.

**Redline action:** Insert a vendor IP indemnification provision: "Vendor will defend, indemnify,
and hold harmless Apollo from and against any third-party claims alleging that the Software
infringes any patent, copyright, trademark, or trade secret of a third party."

---

## Everything Else — No Redline Required

For Category 2 contracts, the following are acceptable as-is and do not require redlines,
regardless of how the vendor has drafted them:

- **Liability cap**: Any reasonable cap is acceptable. Even a relatively low cap (e.g., 3–6
  months of fees) is fine for a tool that handles no personal data and doesn't touch Apollo's
  product.
- **Auto-renewal terms**: Standard auto-renewal with notice windows down to 30 days is
  acceptable. Flag extremely short windows (under 14 days) as YELLOW but do not redline.
- **Termination rights**: Prefer termination for convenience, but absence of one is YELLOW at
  most — not a hard stop for a low-risk tool.
- **Price increases**: Vendor-friendly pricing terms are acceptable. Only flag if pricing is
  genuinely unlimited and unannounced (YELLOW, not RED).
- **Standard limitations of liability**: Vendor disclaimers of consequential damages and other
  standard limitations are acceptable.
- **IP ownership of vendor's software**: Vendor retaining all rights to its platform is fine.

---

## GREEN / YELLOW / RED Assessment Rules

### 🔴 RED — Either hard stop fires:
- Vendor claims ownership of or a broad perpetual license to Apollo's data, configurations,
  or outputs
- Vendor provides zero indemnification to Apollo (completely absent or expressly disclaimed)

### 🟡 YELLOW — No RED, but one or more of:
- Auto-renewal notice window under 14 days (very short — flag for awareness but don't redline)
- No termination for convenience right (flag for awareness; low-risk tool so not critical)
- Price increases unlimited with no advance notice whatsoever (flag for awareness)

### 🟢 GREEN — Both hard stops are clear:
- Apollo's data and outputs are not claimed by the vendor
- Vendor provides some form of indemnification to Apollo

Everything else in this category should come out GREEN.