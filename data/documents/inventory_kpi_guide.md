# Inventory KPI Guide

**Document:** OPS-KPI-INV-001  
**Audience:** Warehouse managers, supply chain analysts  
**Updated:** February 2025

## Purpose

This guide defines key inventory performance indicators (KPIs) used in monthly operations reviews and the executive dashboard.

---

## Inventory Aging

### Definition

**Inventory aging** measures how long inventory has remained in the warehouse without being sold or consumed, expressed in **aging days** from receipt date to the measurement date.

```
Aging Days = Current Date - Receipt Date (for unsold units in stock)
```

### Calculation

- Calculated per SKU per warehouse location.
- Only includes units with status `available` or `reserved`.
- Excludes in-transit and quarantine inventory.

### Thresholds

| Aging Days | Status | Action Required |
|------------|--------|-----------------|
| 0–30 | Healthy | None |
| 31–60 | Watch | Review demand forecast |
| 61–90 | Elevated | Initiate markdown or transfer |
| 91+ | Critical | Mandatory disposition plan within 14 days |

### Reporting

Published weekly in the **Inventory Aging Report** (`inventory_aging.csv`). Branch-level rollups show average aging days and count of SKUs in critical status.

### Target

Company-wide average inventory aging should remain **below 45 days**. Branches exceeding 60-day average trigger a supply chain review.

---

## Inventory Turnover

### Definition

Number of times inventory is sold and replaced over a period.

```
Turnover = Cost of Goods Sold (annual) / Average Inventory Value
```

**Target:** ≥ 6.0 turns per year for fast-moving categories; ≥ 3.0 for slow-moving.

---

## Stockout Rate

### Definition

Percentage of customer orders that could not be fulfilled due to insufficient inventory.

```
Stockout Rate = (Unfulfilled line items due to stock) / (Total line items) × 100
```

**Target:** < 2% monthly.

---

## Fill Rate

Percentage of order lines fulfilled completely from available stock on the first attempt.

**Target:** ≥ 95%.

---

## Dead Stock Percentage

Share of inventory with zero sales in the trailing 180 days.

**Target:** < 5% of total inventory value.

---

## Data Sources

| KPI | Source System | Refresh |
|-----|---------------|---------|
| Inventory Aging | WMS + ERP | Daily |
| Turnover | ERP GL | Monthly |
| Stockout Rate | OMS | Daily |
| Fill Rate | OMS | Daily |
| Dead Stock | WMS + BI | Weekly |

## Contact

Questions about KPI definitions: analytics@company.com
