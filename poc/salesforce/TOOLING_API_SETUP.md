# Tooling API access, sandbox only

What to create so Apex can read Flow internals, real dependency edges and code
coverage. Roughly 15 minutes, needs Setup access. **Nothing here is sent to
anyone.** The Consumer Key and Secret stay in your browser and in Setup; the
POC never sees them and never needs them.

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
