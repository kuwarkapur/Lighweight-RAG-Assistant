# Standard Operating Procedure: Delayed Shipment Escalation

**Document ID:** OPS-SOP-014  
**Version:** 2.1  
**Effective Date:** January 2025  
**Owner:** Logistics Operations

## Purpose

This SOP defines the escalation process when customer shipments are delayed beyond committed delivery windows.

## Definitions

- **Delayed shipment:** Any shipment that has not been delivered within the promised delivery date (PDD) plus a 24-hour grace period.
- **Critical delay:** Shipment delayed by more than 72 hours past PDD.
- **SLA breach:** Delay exceeding the contractual service level agreement threshold.

## Escalation Levels

### Level 1 — Operations Coordinator (0–24 hours past PDD)

1. Identify delayed shipments via the TMS dashboard (filter: `status=delayed`).
2. Contact the carrier for updated ETA within 2 business hours.
3. Notify the customer via automated email with revised delivery estimate.
4. Log the incident in the Shipment Exception Register (SER).

**Responsible party:** Shift Operations Coordinator  
**Response time:** Within 2 hours of detection

### Level 2 — Regional Logistics Manager (24–72 hours past PDD)

Triggered automatically when a Level 1 case remains unresolved after 24 hours.

1. Review root cause (carrier capacity, weather, customs hold, warehouse backlog).
2. Authorize expedited re-routing or alternate carrier if cost impact is under $500.
3. Assign a dedicated customer liaison for proactive updates every 12 hours.
4. Escalate to Level 3 if no resolution within 48 hours at this level.

**Responsible party:** Regional Logistics Manager  
**Approval required for costs:** Up to $500 without VP sign-off

### Level 3 — VP Supply Chain (72+ hours / Critical delay)

1. Executive review of carrier performance and contractual penalties.
2. Approve emergency air freight or cross-dock alternatives (any cost).
3. Initiate formal carrier claim if carrier fault is documented.
4. Customer compensation per Policy FIN-COMP-003 (credit, refund, or replacement).

**Responsible party:** VP Supply Chain  
**Notification:** CEO office informed for delays affecting top-10 accounts

## Communication Templates

Use template `COMM-DELAY-L1`, `COMM-DELAY-L2`, or `COMM-DELAY-L3` from the communications library based on escalation level.

## Reporting

All escalations must be closed in SER within 5 business days of resolution. Weekly summary sent to ops-leadership@company.com every Monday 9:00 AM.

## Exceptions

International customs delays follow SOP OPS-SOP-022 (Customs Hold Escalation) instead of this procedure when the hold reason is `customs_inspection`.
