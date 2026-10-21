# Linode Support Ticket — Request additional IPv4 for srv-3388

**Draft. Review for tone and accuracy before submitting via https://cloud.linode.com/support/tickets.**

---

**Subject:** IPv4 limit increase — srv-3388 (ID 108535580) — outbound mail relay with per-IP quota requirements

**Linode / Account:** srv-3388, Linode ID `108535580`, region `ap-southeast` (Sydney), primary IPv4 `172.105.167.140`.

**Request:** Please add **4 additional public IPv4 addresses** (total 5 on this Linode) to srv-3388.

**Technical justification:**

I operate an outbound mail relay (PowerMTA) that forwards authenticated submission through my own Microsoft 365 / Exchange Online tenant for the domain `zabo.com`. I am the Exchange administrator for the tenant.

Microsoft Exchange Online Protection (EOP) enforces a strict **per-source-IPv4 recipient throttle** (~2,544 recipients per throttle window, returning `451 4.7.500 Access denied, please try again later. (AS2162)`). This is documented EOP behaviour for IP-reputation / graylisting throttling and is independent of my relay configuration — it is scoped to the source IPv4 the connection originates from.

I have verified experimentally that:

- Two distinct IPv4 addresses on **separate** Linodes yield ~5,088 recipients per window (quotas **stack per distinct IPv4**).
- Ten IPv6 addresses across ten different /64s inside a /56 still yield ~2,544 (EOP throttles the entire IPv6 **range** as one sender). IPv6 is not a viable scaling path for this workload.

The direct, documented path to higher throughput is therefore additional IPv4 source addresses. I would prefer to keep this workload on a single, correctly-tuned host (one PowerMTA instance, one `*.zabo.com` wildcard certificate, one SPF record maintenance surface, one DKIM key) rather than fan out across five separate Nanodes, which would:

- Multiply the operational surface (five hosts to patch, monitor, and secure).
- Require five sets of PTR/A-record maintenance in DNS Made Easy and the Linode panel.
- Make certificate renewal and PMTA upgrades five times the work for identical gain.

**Technical readiness on my side:**

- Each additional IPv4 will receive a dedicated `mtaN.zabo.com` **PTR** record (set via the Linode panel) and matching **A record** (DNS Made Easy), satisfying FCrDNS.
- All addresses are added to the single `zabo.com` **SPF** record (one TXT record, no duplicates) and share the existing **DKIM** key/selector.
- The `*.zabo.com` wildcard certificate on the host is IP-agnostic, so the M365 authenticated inbound connector will accept connections from every IPv4 attached to srv-3388 without additional connector configuration.
- Outbound submission is already configured through TLS on port 587 with authenticated STARTTLS.

**Reverse-DNS commitment:** PTR records will be set within 24 hours of each IPv4 being assigned, and will remain within the `zabo.com` domain. No PTR will be left pointing to a generic `linode.com` hostname.

**Address count:** 4 additional (5 total). Happy to accept a smaller allocation initially and request further addresses later as deliverability data from the first allocation is reviewed.

If any of the above is insufficient — in particular if you would prefer the request be sized to actual sent volume over the last 30 days, or scoped per-month rather than permanently — please let me know what you need and I will provide it.

Thanks,
[your name] — tenant admin, `zabo.com`
