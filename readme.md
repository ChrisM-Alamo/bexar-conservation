# Bexar County Ecological Monitoring & Conservation Maps

This project translates community science data from **iNaturalist** into interactive conservation maps for **Bexar County, Texas**. 

By grouping thousands of field observations into standardized spatial grids, these maps help our Master Naturalist chapter, local land trusts, and preserve managers answer two key questions:
1. **Where are our biodiversity data gaps?**
2. **Where are high-priority invasives directly threatening sensitive species?**

---

## How to Read the Maps

Both maps divide Bexar County into **hexagonal survey cells** (H3 resolution 8). Each hexagon covers roughly **170 acres** (about 0.7 km²), an ideal scale for evaluating city parks, natural areas, and watershed corridors.

Use the layer control panel in the **top-right corner** of each map to toggle views on or off.

---

### Map 1: Biodiversity & Survey Gaps

* **Species Richness (Choropleth Layer):** 
  * Displays total documented biodiversity across all kingdoms (plants, insects, birds, fungi, reptiles).
  * **Color Scale:** Pale yellow indicates fewer unique species recorded; deep teal/blue indicates high documented species counts (e.g., Friedrich Wilderness Park, Hardberger Park, Mitchell Lake).
* **Bio-Gaps (<= 5 Observations in 12 Months):**
  * Highlights hexagons that have 5 or fewer Research Grade observations over the past year.
  * **How to use it:** Look for green corridors, creek drainages, and public easements on the USGS topographic base map that sit inside these orange cells. These represent prime targets for chapter mini-BioBlitzes and targeted field surveys.

---

### Map 2: Invasives vs. SGCN Threats

* **Invasive Species (Pressure Layer):**
  * Flags cells containing confirmed observations of high-priority regional invasives (e.g., Bastard Cabbage, Privet, Chinaberry, Giant Reed, King Ranch Bluestem, Applesnails).
  * **Tooltip:** Hovering over a cell shows the exact invasive species documented inside that boundary.
* **Texas SGCN (Refugia Layer):**
  * Highlights cells containing **Species of Greatest Conservation Need** as designated by Texas Parks & Wildlife (TPWD), such as the Golden-cheeked Warbler, Texas Horned Lizard, Texas Tortoise, and endemic Edwards Aquifer/karst fauna.
* **Direct Threat (Overlap Layer):**
  * Displays cells in **bright magenta** where rare or monitored native species share immediate territory with documented high-priority invasives.
  * **How to use it:** These cells represent high-priority zones for habitat restoration and invasive management workdays.

---

## Data Source & Methodology

* **Data Feed:** [iNaturalist Research Grade Observations](https://www.inaturalist.org/) within Bexar County (Place ID: `49994`) over a rolling 12-month window.
* **Spatial Binning:** Uber's open-source H3 Discrete Global Grid System.
* **Base Map:** U.S. Geological Survey (USGS) National Map Topographic Service.

---

*Curated by the Texas Master Naturalist community. For questions, suggestions, or to request custom species filters, open an issue in this repository.*
