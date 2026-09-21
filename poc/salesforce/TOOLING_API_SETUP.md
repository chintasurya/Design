# Tooling API access, sandbox only

What to create so Apex can read Flow internals, real dependency edges and code
coverage. Roughly 15 minutes, needs Setup access. **Nothing here is sent to
anyone.** The Consumer Key and Secret stay in your browser and in Setup; the
POC never sees them and never needs them.

---

## Read this first: which path applies to you

There are two ways to authenticate, and **the org decides which one is
available**, not preference.

Look at **External Client App → Settings → OAuth → Security → Require Proof Key
for Code Exchange (PKCE) extension for Supported Authorization Flows**.

| What you see | Path |
|---|---|
| The checkbox is editable | Either works. Sections 1 to 5 below (authorization code) are fewer screens. |
| **Greyed out, with "To change this required setting, contact Support"** | **Authorization code is not available.** A Salesforce-type Auth. Provider does not send a `code_challenge`, so saving the Named Credential fails with `missing required code challenge` and no setting you control will fix it. **Go straight to Appendix A: Client Credentials.** |

Client Credentials is not a workaround. It never redirects a browser, so PKCE
does not apply; it has no refresh token to expire or rotate; and it works in
asynchronous Apex, which the graph export needs anyway. If the org locks PKCE
on, this was always the right destination.

---

## One correction before you start

You asked for `test.salesforce.com` throughout. It is right in one place and
wrong in the other, and the wrong one fails in a way that is hard to diagnose.

| Where | Use | Why |
|---|---|---|
| Auth. Provider **Authorize** and **Token** endpoints | `https://test.salesforce.com/...` | This is a **login** host. Sandboxes authenticate here. Correct. |
| Named Credential **URL** | `https://<mydomain>--<sandbox>.sandbox.my.salesforce.com` | This is an **API** host. `test.salesforce.com` serves login pages, not `/services/data`. Pointing a Named Credential at it returns a redirect to a login page, and the callout fails with a 302 or an HTML body instead of JSON. |

Find your My Domain URL at **Setup → Company Settings → My Domain →
Current My Domain URL**, or just read it out of the browser address bar while
you are in the sandbox. It ends in `.sandbox.my.salesforce.com`.

Everything below is sandbox. No step here touches production.

---

## 1. External Client App

Salesforce replaced Connected Apps with External Client Apps. The Auth.
Provider and Named Credential steps are unchanged; only the app definition
moved.

**Setup → App Manager → New External Client App**
(or **Setup → External Client App Manager → New External Client App**)

### Basic Information

| Field | Value |
|---|---|
| External Client App Name | `AI Tooling API` |
| API Name | `AI_Tooling_API` |
| Contact Email | yours |
| Distribution State | **Local** |

`Local` matters: it means the app lives in this org only and is not packaged
for distribution. A packaged app asks for things you do not need.

### API (Enable OAuth Settings)

Tick **Enable OAuth**.

| Field | Value |
|---|---|
| Callback URL | `https://login.salesforce.com/services/oauth2/success` (a placeholder, replaced in step 3) |
| Selected OAuth Scopes | **Manage user data via APIs (api)** and **Perform requests at any time (refresh_token, offline_access)** |
| Require Secret for Web Server Flow | **checked** |
| Require Secret for Refresh Token Flow | **checked** |
| Require Proof Key for Code Exchange (PKCE) | **unchecked** |

Untick PKCE. A Salesforce-type Auth. Provider does not always send a PKCE
challenge, and if the app demands one the authorization fails with an opaque
error at the last step of step 4. If your org policy requires PKCE, leave it on
and expect to debug that specific failure.

Save.

### Policies — do not skip this

External Client Apps split **Settings** from **Policies**, and a newly created
app has its policies unconfigured. This is the single most common reason a
correctly built app refuses to authorize.

**External Client App Manager → `AI Tooling API` → Policies → Edit**

| Setting | Value |
|---|---|
| Enable OAuth | **checked** (it is a second, separate switch from the one in Settings) |
| Permitted Users | *Admin approved users are pre-authorized* — then assign the app to your profile or a permission set. Or *All users may self-authorize* if you would rather not. |
| IP Relaxation | **Relax IP restrictions** |
| Refresh Token Policy | **Refresh token is valid until revoked** |

Save.

### Consumer Key and Secret

**Settings → OAuth Settings → Consumer Key and Secret**. You may be asked for a
verification code sent to your email.

Copy both somewhere local. **Do not paste them into this chat, a ticket, or
the repo.** They are only needed in step 2, on the next screen.

**Wait about ten minutes** before step 4. New app credentials take that long to
propagate, and authorizing too early fails with `invalid_client_id` even though
everything is correct.

---

## 2. Auth. Provider

**Setup → Auth. Providers → New → Provider Type: Salesforce**

| Field | Value |
|---|---|
| Name | `AI Tooling Auth` |
| URL Suffix | `AI_Tooling_Auth` |
| Consumer Key | from step 1 |
| Consumer Secret | from step 1 |
| Authorize Endpoint URL | `https://test.salesforce.com/services/oauth2/authorize` |
| Token Endpoint URL | `https://test.salesforce.com/services/oauth2/token` |
| Default Scopes | `api refresh_token` |

Leave the registration handler and execute-as fields empty. Save.

---

## 3. Copy the callback URL back

Saving the Auth. Provider generates a **Callback URL** at the bottom of its
detail page, of the form
`https://<mydomain>.sandbox.my.salesforce.com/services/authcallback/AI_Tooling_Auth`.

Copy it, go back to **External Client App Manager → `AI Tooling API` →
Settings → API (Enable OAuth Settings) → Edit**, and replace the placeholder
callback URL with it. Save.

If the Auth. Provider page shows more than one callback URL, take the one
containing `/services/authcallback/`.

---

## 4. Named Credential

**Setup → Named Credentials → New → New Legacy**

"Legacy" is deliberate. The newer External Credential model works too, but it
is three objects instead of one and the field labels have moved between
releases. Legacy is one screen and is not deprecated for this use.

| Field | Value |
|---|---|
| Label | `AI Tooling API` |
| Name | `AI_Tooling_API` |
| URL | `https://<mydomain>--<sandbox>.sandbox.my.salesforce.com` — **your My Domain, not test.salesforce.com** |
| Identity Type | **Named Principal** |
| Authentication Protocol | **OAuth 2.0** |
| Authentication Provider | `AI Tooling Auth` |
| Scope | `api refresh_token` |
| Start Authentication Flow on Save | **checked** |
| Generate Authorization Header | **checked** |
| Allow Merge Fields in HTTP Header | unchecked |
| Allow Merge Fields in HTTP Body | unchecked |

Save. The browser redirects to a Salesforce login and an approval screen. Log
in **as the sandbox user whose access you want the callouts to run with**, and
approve.

Named Principal means every callout runs as that one user regardless of who
triggered it. That is what makes the graph build reproducible: the same export
reads the same metadata no matter who pressed the button.

When it returns, the Named Credential detail page should show
**Authentication Status: Authenticated as &lt;user&gt;**. If it shows
*Pending* or an error, nothing below will work — fix it before going on.

No Remote Site Setting is needed. A Named Credential covers that.

---

## 5. Permissions on that user

The user you authorized as needs, via profile or permission set:

| Permission | Why |
|---|---|
| **API Enabled** | Any callout at all |
| **View Setup and Configuration** | Reading Tooling API metadata objects |
| **View All Data** | `MetadataComponentDependency` refuses without it |

`View All Data` is a wide permission. It is read-only, it is a sandbox, and the
dependency API genuinely requires it. If that is not acceptable, say so and we
drop dependency edges and keep the rest — flow internals do not need it.

---

## 6. Record the credential name in config — optional today

**Setup → Custom Metadata Types → AI POC Config → Manage Records → Default →
Edit → Tooling Named Credential = `AI_Tooling_API` → Save.**

If no `Default` record exists, click **New** and fill in that one field.

**Be clear about what this does: nothing, yet.** No Apex reads
`Tooling_Named_Credential__c` at the moment. The field exists so the flow
reader has somewhere to look when it is built, and so that a differently named
credential does not mean a code change later. Step 7 does not depend on it and
neither does anything deployed today.

If your Named Credential is named exactly `AI_Tooling_API`, you can skip this
step entirely and lose nothing.

---

## 7. Verify before anything is built on it

This is the step that matters.

Run `tools/verify_tooling_api.apex` in **Developer Console → Debug → Open
Execute Anonymous Window**, tick **Open Log**, press **Execute**. Read-only:
five GET callouts, nothing written anywhere.

If your credential is named something other than `AI_Tooling_API`, change the
`CREDENTIAL` value on the first line of the script. That string, not the custom
metadata record, is what the script uses.

### What each line of the output means

| Line | Good result | What a bad one means |
|---|---|---|
| **1. connectivity** | `HTTP 200` and a JSON body | `HTTP 401` → the credential is not authenticated; open it in Setup and check it says *Authenticated as &lt;user&gt;*. `HTTP 403` → that user lacks API Enabled or View Setup and Configuration. A body starting `<` → it is an HTML login page, so the Named Credential URL is test.salesforce.com instead of My Domain. A callout exception before any response → no credential by that name. |
| **2. active flows** | `totalSize: <n>` | That number is the size of the job: how many flow bodies have to be read to see what the flows do. |
| **3. flow metadata** | `mentions recordCreates: true` | This is the whole point of the setup. `true` means HFN generation done in Flow becomes visible. `false` on a flow that does create records would mean the retrieve is not returning what we expect. |
| **4. SELECT Metadata, LIMIT 5** | either answer is useful | `200` means several flows can be read per call and the reader is simple. A non-200 confirms one-per-call, so reading every flow needs a chained Queueable across transactions. |
| **5. dependency API** | `HTTP 200` | Non-200 usually means no View All Data. **Not a blocker on its own** — flow internals do not need it. It only costs real dependency edges. |

The script stops after step 1 if connectivity fails, rather than printing the
same error five times.

**Send me the whole log.** Nothing gets built against this until that output
exists: every assumption in the table above is worth checking rather than
trusting, and line 4 in particular changes how much work the flow reader is.

---

## What this unlocks

| Query | What it gives |
|---|---|
| `Flow.Metadata` | what a flow **does** — `recordCreates`, `recordUpdates` and their targets. The HFN-generated-by-Flow half of the picture |
| `Flow.Metadata` subflow elements | flow-to-subflow chains, the equivalent of the Apex call edges already built |
| `MetadataComponentDependency` | real dependency edges, replacing the Apex body text scan |
| `ValidationRule`, `LightningComponentBundle` | two component types the graph cannot see at all today |
| `ApexCodeCoverageAggregate` | coverage, needed for the deploy gate later |

## The constraint to plan around

Tooling API queries that select `Metadata` or `FullName` return **one record
per call**. With ~200 active flows that is 200 callouts against a limit of 100
per transaction, so flow internals have to be read in a chained Queueable
across several transactions, with progress persisted between them.

This is the current understanding and it is exactly what step 7 checks. If it
turns out `Metadata` can be selected for several records at once, the reader
gets much simpler.


---

## Troubleshooting: `HTTP 401` with `INVALID_SESSION_ID`

```
1. connectivity · HTTP 401
   body: [{"message":"Session expired or invalid","errorCode":"INVALID_SESSION_ID"}]
```

**Read the good news in that first.** The body is a real Salesforce API error
in JSON, not an HTML login page, so:

- the Named Credential exists under the name the script used;
- its URL is right — the request reached the API, which `test.salesforce.com`
  would never have done;
- the endpoint and API version are right.

One thing is missing: a valid token on the request. Work through these in
order, because the first is by far the most common.

### 1. New-model Named Credential with no principal access

If the Named Credential screen had a field called **External Credential**, you
created the new-model credential rather than the legacy one. In that model the
token is held by a **Principal** on the External Credential, and a running user
gets nothing at all until that principal is granted to them through a
permission set. No grant, no token, `INVALID_SESSION_ID` — exactly this error.

**Setup → Permission Sets →** pick one assigned to you (or create one) **→
External Credential Principal Access → Edit → add the principal belonging to
your External Credential → Save.** Then assign that permission set to yourself
and run the script again.

### 2. The credential never completed authentication

**Setup → Named Credentials → `AI Tooling API`.** A legacy credential shows
**Authentication Status**. If it is blank, *Pending*, or shows an error, no
token was ever obtained.

Fix: **Edit → tick Start Authentication Flow on Save → Save**, and complete the
login and approval in the window that opens. It must come back reading
**Authenticated as &lt;user&gt;**.

### 3. Identity Type is Per User

Per User means every user authenticates separately, and you are running as a
user who has not. Set **Identity Type = Named Principal** and re-authenticate.
Named Principal is what the export needs anyway: the graph must read the same
metadata no matter who triggers it.

### 4. Generate Authorization Header is unchecked

Then Salesforce attaches no `Authorization` header and the request arrives
anonymous. Tick it.

### 5. The refresh token was revoked or expired

If the External Client App's **Refresh Token Policy** is anything other than
*valid until revoked*, the token can die between setup and use. Set it to valid
until revoked, then re-authenticate the credential.

---

## Not blocked by any of the above

`tools/verify_tooling_session.apex` answers the same five questions using
`UserInfo.getSessionId()` instead of the Named Credential, so what the Tooling
API actually returns can be established while the OAuth configuration is still
being chased.

It needs one thing: **Setup → Security → Remote Site Settings → New**, with the
My Domain URL the script prints on its first line. Delete that remote site once
the Named Credential works.

**It is a diagnostic, not the production path.**
`UserInfo.getSessionId()` returns a usable session in an interactive anonymous
block but does not reliably return an API-enabled one in asynchronous Apex, and
the graph export is a Queueable. The Named Credential still has to work before
the flow reader can ship. This only stops the question "is this data worth
having" waiting on the question "is the OAuth config right".


---

## Troubleshooting: `missing required code challenge` when saving the Named Credential

```
error=invalid_request&error_description=missing%20required%20code%20challenge
```

The authorization flow started, reached the External Client App, and the app
demanded a PKCE `code_challenge` that the Salesforce-type Auth. Provider did
not send. Nothing is wrong with the URLs, the key, the secret or the callback:
the two ends disagree about PKCE.

**Unticking PKCE on the app is often not enough, because there are two
switches and the org-wide one wins.**

### Turn it off in both places

1. **Org-wide.** Setup → **OAuth and OpenID Connect Settings** → find
   **Require Proof Key for Code Exchange (PKCE) Extension for Supported
   Authorization Flows** and turn it **off**. This is the one people miss. If
   it is on, the app-level setting cannot save you.
2. **On the app.** External Client App Manager → `AI Tooling API` → Settings →
   OAuth → **Require Proof Key for Code Exchange (PKCE)** → unticked. On some
   releases this sits under a **Security** subsection of the OAuth settings.

Then **wait about ten minutes** — app changes propagate on the same delay as a
new Consumer Key — and re-save the Named Credential with **Start
Authentication Flow on Save** ticked.

### If org policy will not allow PKCE to be disabled

See **Appendix A** below. That is the whole answer: client credentials never
sends a code challenge, so the setting stops mattering.

### Neither of these is blocking the POC today

`tools/verify_tooling_session.apex` answers the five Tooling API questions with
no OAuth at all. Run that first so the flow reader can be designed against real
output while this is being sorted out.


---

# Appendix A: Client Credentials

Use this when PKCE is locked on, or whenever you would rather not depend on a
browser authorization and a rotating refresh token. There is no redirect, no
authorization code and no `code_challenge`, so the PKCE setting is simply not
in the conversation.

The shape, so the steps make sense even if a label has moved between releases:

```
External Client App          enables the flow and names a Run As user
        ↓  client id + secret
External Credential          holds the token, one Principal
        ↓  granted by
Permission Set               External Credential Principal Access
        ↓  used by
Named Credential             points at the org's My Domain URL
```

Skipping the permission set is the most common mistake and produces
`INVALID_SESSION_ID`, not a permissions error, which sends people looking in
the wrong place.

## A1. External Client App

**An External Client App has two separate screens and they do different jobs.
Everything in this step is on the second one.**

| Screen | What lives there |
|---|---|
| **Settings** | *Flow Enablement* and *Security*. Declares which flows the app is capable of. **No Run As field exists here** — if you are looking at a page with the Security checkboxes on it, you are on the wrong tab. |
| **Policies** | *OAuth Policies*. Declares how the app behaves at runtime, including **Run As**. |

### First, on Settings

**External Client App Manager → `AI Tooling API` → Settings → OAuth →
Flow Enablement**

| Setting | Value |
|---|---|
| Enable Client Credentials Flow | **checked** |
| Enable Authorization Code and Credentials Flow | not needed |

Save.

### Then, on Policies — this is where Run As is

**External Client App Manager → `AI Tooling API` → Policies → Edit**

**Click Edit before looking for anything.** The Policies tab opens read-only,
and read-only here means every field is greyed out — Permitted Users, IP
Relaxation, Apex Plugin Class, Refresh Token Validity Unit and the Enable
Client Credentials Flow checkbox all at once. That looks exactly like a
feature the org does not have, and it is not: it is a form waiting for the
Edit button.

The tell is that **everything** is grey. A genuinely unavailable setting is
greyed on its own, with a note beside it like *"To change this required
setting, contact Support"* — which is what PKCE looks like on the Settings
tab. A whole panel greyed together is just view mode.

**Run As renders only after the checkbox is ticked**, not before, so the order
is: Edit → tick Enable Client Credentials Flow → the Run As lookup appears →
choose the user → Save.

If the Policies screen looks empty, or shows no OAuth section at all, look for
an **Enable OAuth Policies** toggle and turn it on first. A new app's policies
are unconfigured, and the OAuth section only renders once they exist.

If the checkbox stays greyed **in edit mode**, the Settings-tab flow enablement
has not propagated yet. Wait ten minutes and reload.

| Setting | Value |
|---|---|
| Enable Client Credentials Flow | **checked** — a second switch with the same name as the Settings one, doing a different job |
| **Run As** | the user the callouts should run as |
| Permitted Users | if *Admin approved users are pre-authorized*, the Run As user must have the app assigned through their profile or a permission set |
| IP Relaxation | **Relax IP restrictions** |

Save.

**If Run As still does not appear** after saving Settings and enabling OAuth
policies: reload the page rather than navigating back to it, since the section
is rendered from the saved flow enablement, and give it a few minutes. The same
propagation delay that affects a new Consumer Key applies here.

**If it never appears**, the flow cannot be completed and the remaining option
that avoids PKCE is **JWT Bearer** — also in the Flow Enablement list. It names
its user through the JWT subject rather than a Run As field, at the cost of
needing a certificate. Say so and that path gets written up; do not spend an
afternoon hunting for a field that this release may simply not render.

**The Run As user is the identity every callout uses.** It needs **API
Enabled**, **View Setup and Configuration**, and **View All Data** if
dependency edges are wanted. Pick a user whose access you are happy to have
the graph build read with, because it will read exactly that and nothing more.

### The warning Salesforce shows when you tick this

> *Anyone with the consumer key and consumer secret can access your org on
> behalf of the selected user.*

That is not boilerplate, it is the honest security property of this flow, and
it is the price of not needing a browser. The key and secret together are a
**bearer credential**: whoever holds both can obtain a token as the Run As
user, with no login, no MFA and no human in the loop. There is no second
factor to fall back on.

Click OK, then contain it:

| Do | Why |
|---|---|
| **Sandbox only.** Never build the equivalent app in production. | Everything in this POC is sandbox-scoped by rule. This is the step where breaking that rule would cost the most. |
| **Use a dedicated integration user**, not a person's login | Revoking it later breaks nothing a human depends on, and the audit trail says "the graph build did this" rather than naming someone who was asleep at the time |
| **Grant the minimum.** API Enabled and View Setup and Configuration are required. **View All Data is not** | It is needed only for `MetadataComponentDependency`. Drop it and the only thing lost is real dependency edges; flow internals, which are the point, do not need it |
| **Never put the secret in git, a ticket, a chat or this conversation** | It is Setup-to-Setup only. The POC never reads it and never needs it |
| **Delete the External Client App when the POC ends** | A standing bearer credential with no owner is the thing that turns up in an audit two years later |

If View All Data is not acceptable in your org, say so rather than granting it
quietly. The graph loses dependency edges and keeps everything else.

Copy the **Consumer Key** and **Consumer Secret** from
**Settings → OAuth Settings → Consumer Key and Secret**, and wait about ten
minutes before A2 so they propagate.

## A2 and A5 are two different objects. This is the part that trips everyone.

They live on two tabs of the same Setup page, both are created with a button
called **New**, both ask for a **URL**, and the two URLs are different. Putting
the token endpoint on the Named Credential is the single easiest mistake to
make here.

| | **External Credential** (A2) | **Named Credential** (A5) |
|---|---|---|
| Answers | *how do I get a token* | *where do I send the request* |
| Created at | Named Credentials → **External Credentials** tab → New | Named Credentials → **Named Credentials** tab → New |
| Label / Name | `AI Tooling Cred` / `AI_Tooling_Cred` | `AI Tooling API` / `AI_Tooling_API` |
| URL | the **token endpoint**: `https://test.salesforce.com/services/oauth2/token` | the **API host**: `https://<mydomain>--<sandbox>.sandbox.my.salesforce.com` |
| Holds | the flow type, and the principal with the client id and secret | the External Credential lookup, and Generate Authorization Header |

The Named Credential form has a required **External Credential** field. It
cannot be filled until A2 exists, so **A2 is built first, always.** A New Named
Credential form that will not save because that field is empty is not a
problem with the form; it is the order.

`AI_Tooling_API` is the name the probe scripts call. That name belongs to the
**Named Credential**, never to the External Credential.

## A2. External Credential

**Setup → Named Credentials → External Credentials tab → New**

| Field | Value |
|---|---|
| Label | `AI Tooling Cred` |
| Name | `AI_Tooling_Cred` |
| Authentication Protocol | **OAuth 2.0** |
| Authentication Flow Type | **Client Credentials with Client Secret** |
| Identity Provider URL (token endpoint) | `https://test.salesforce.com/services/oauth2/token` |
| Scope | `api` |

This is the one place `test.salesforce.com` is correct in this appendix: it is
the token endpoint, a login host doing what login hosts do.

Save.

## A3. Principal

On the saved External Credential, **Principals → New**.

| Field | Value |
|---|---|
| Parameter Name | `Tooling` |
| Sequence Number | `1` |
| Client ID / Consumer Key | from A1 |
| Client Secret / Consumer Secret | from A1 |

Depending on release these are either two named fields or two rows in an
**Authentication Parameters** list, in which case the names are `client_id`
and `client_secret`. Save.

## A4. Grant the principal — the step everyone misses

A principal is inert until a running user is granted it. Without this the
callout carries no token and returns
`[{"message":"Session expired or invalid","errorCode":"INVALID_SESSION_ID"}]`,
which reads like an authentication failure rather than a missing grant.

**Setup → Permission Sets →** pick or create one **→ External Credential
Principal Access → Edit → add `AI_Tooling_Cred - Tooling` → Save.**

Assign that permission set to **yourself** (so the probe scripts work) and to
whoever or whatever triggers the graph build.

### If that section shows zero records

It is listing **principals**, and a permission set can only grant a principal
that already exists. Check these in order.

The list is alphabetical and every row reads
`<External Credential> - <Principal>`, so `AI_Tooling_Cred - Tooling` sorts
near the top. If the list starts at something like `GCP_...` and there is no
`AI_...` row above it, the principal does not exist — that is a certainty, not
a guess, and there is no point scrolling.

**1. Does the External Credential have a Principal at all?**

Setup → Named Credentials → **External Credentials** tab → `AI Tooling Cred` →
the **Principals** section should contain a row named `Tooling`. If it is
empty, A3 has not been done and there is nothing to grant. Create the principal
first; this section will stay empty forever otherwise.

This is the most common cause, because A4 reads like the next click after A2
and it is easy to pass straight over A3.

**2. Are you looking at the granted list rather than the picker?**

That section shows what is **already enabled**, which is legitimately zero on a
new permission set. The available principals only appear once you click
**Edit**, in the usual two-box Available / Enabled picker. Zero records in view
mode means nothing has been granted yet, not that nothing can be.

**3. Did you create an External Credential, or a Legacy Named Credential?**

Legacy named credentials hold their own authentication and have no principals,
so nothing about them ever appears here. If the credential you made had
**Authentication Protocol** and **Authentication Provider** fields on the same
screen as the URL, it is the legacy one. Client credentials needs the
**External Credential** plus **Named Credential** pair from A2 and A5.

### A working example already exists in this org

This picker lists every principal in the org, and there are around nineteen of
them — `NPI_Registry_EC`, `NextGate_EMPI_API_PROD`, `PatientEncounters_API_QA`
and so on. So the new External Credential model is already in use here and
somebody has made it work before.

Open one from **Setup → Named Credentials → External Credentials** and look at
how its principal is laid out before building `AI Tooling Cred`. The
authentication protocols differ, since those point at outside APIs rather than
at this org, but the shape — external credential, named principal, parameters —
is identical, and a working example in the same org beats a runbook written
against a different release.

## A5. Named Credential

**Setup → Named Credentials → New** — the button labelled plain **New**, not
**New Legacy**. They sit next to each other and produce different objects. The
legacy form is the one with *Authentication Protocol*, *Authentication
Provider* and *Authentication Status* on it; the new form has an **External
Credential** lookup instead and no status field at all, because there is
nothing interactive to report.

**A legacy credential cannot be converted.** If one already exists under the
name you want, delete it first: the name `AI_Tooling_API` is what the probe
scripts call, and two credentials cannot share it.

Deleting it is safe. It holds no token — that is what *Pending* means — and
nothing in the POC references it yet. The `AI Tooling Auth` Auth. Provider can
stay; it is unused by the client credentials flow and harmless.

**Leave no trailing slash on the URL.** The scripts append
`/services/data/v59.0/...`, so a URL ending in `/` produces a double slash in
the path. It is usually tolerated and occasionally is not, and it costs
nothing to avoid.

| Field | Value |
|---|---|
| Label | `AI Tooling API` |
| Name | `AI_Tooling_API` |
| URL | `https://<mydomain>--<sandbox>.sandbox.my.salesforce.com` — **My Domain, never test.salesforce.com** |
| Enabled for Callouts | **checked** |
| External Credential | `AI Tooling Cred` |
| Generate Authorization Header | **checked** |
| Allow Formulas in HTTP Header | unchecked |
| Allow Formulas in HTTP Body | unchecked |

## A5b. "Authentication Status: Pending" — what it means here

**Client credentials has no interactive authentication step.** There is no
browser redirect, no approval screen and no Authenticate button to press. A
token is fetched on the first callout and not before. So a status stuck at
*Pending* is never something to wait out or click through: it means something
in the chain is still configured for the browser flow.

Find which, by where the word appears.

| Where *Pending* is shown | What it means | Fix |
|---|---|---|
| On the **Named Credential** detail page, as **Authentication Status**, next to fields called *Authentication Protocol* and *Authentication Provider* | This is a **Legacy** named credential. Legacy holds its own OAuth and cannot use an External Credential, so it is running the browser flow — the one PKCE blocks in this org. | Delete it. Create a standard Named Credential (A5) whose **External Credential** field points at `AI Tooling Cred`. |
| On the **External Credential → Principals** row | The External Credential's **Authentication Flow Type** is **Browser Flow**, not **Client Credentials with Client Secret**. Browser flow is what shows a status and offers an Authenticate action, and that action will fail on PKCE. | Edit the External Credential, set the flow type to **Client Credentials with Client Secret**, set the token endpoint to `https://test.salesforce.com/services/oauth2/token`, and make sure the principal carries the **Client ID** and **Client Secret**. |

### Do not chase the label. Run the callout.

Once the flow type is client credentials, the status field is either absent or
meaningless, because there is no interactive step for it to describe. Status
labels in this area differ between releases and several of them are misleading.

**The only test that means anything is whether a request comes back with a
token.** Run A6. An `HTTP 200` is a working credential no matter what any
screen says about it, and a `401` is a broken one no matter how reassuring the
status looks.

## A6. Verify

Run `tools/verify_tooling_api.apex`. There is no authentication status to
check on this model and nothing to click through: the first callout either
returns a token-backed `HTTP 200` or it does not.

| Result | Meaning |
|---|---|
| `HTTP 200` | Done. Send the log. |
| `HTTP 401 INVALID_SESSION_ID` | The permission set grant in A4 is missing, or not assigned to you |
| `HTTP 403` | The **Run As** user lacks API Enabled or View Setup and Configuration |
| Body starts with `<` | The Named Credential URL is a login host, not My Domain |
| Callout exception | No Named Credential by that name |
