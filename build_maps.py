import time
from datetime import datetime, timedelta
import pandas as pd
import h3
import folium
from folium.features import GeoJsonTooltip
import branca.colormap as cm
from pyinaturalist import get_observations

BEXAR_PLACE_ID = 49994
H3_RESOLUTION = 8

TEXAS_INVASIVES = [
    "Ligustrum", "Nandina domestica", "Melia azedarach", "Triadica sebifera",
    "Arundo donax", "Tamarix", "Pyrus calleryana", "Broussonetia papyrifera",
    "Vitex agnus-castus", "Leucaena leucocephala", "Rapistrum rugosum",
    "Bothriochloa ischaemum", "Sorghum halepense", "Cenchrus ciliaris",
    "Lonicera japonica", "Macfadyena unguis-cati", "Colocasia esculenta",
    "Eichhornia crassipes", "Hydrilla verticillata", "Dreissena polymorpha",
    "Pomacea maculata", "Solenopsis invicta", "Sus scrofa", "Myocastor coypus",
    "Hypostomus", "Pterygoplichthys"
]

TEXAS_SGCN = [
    "Setophaga chrysoparia", "Vireo atricapilla", "Lanius ludovicianus",
    "Ammodramus savannarum", "Melanerpes erythrocephalus", "Phrynosoma cornutum",
    "Eurycea", "Sceloporus arenicolus", "Gopherus berlandieri", "Crotalus horridus",
    "Cicurina venii", "Rhadine", "Batrisodes venyivi", "Stygobromus",
    "Dionda diaboli", "Campostoma anomalum", "Streptanthus brauntonii",
    "Batesimalva violacea", "Strophostyles leiosperma", "Spigelia texana"
]

one_year_ago = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
print(f"Fetching Bexar County observations since {one_year_ago}...")

records = []
# Pull up to 50 pages (10,000 observations) to stay comfortably within workflow limits
MAX_PAGES = 50 

for page in range(1, MAX_PAGES + 1):
    resp = get_observations(
        place_id=BEXAR_PLACE_ID,
        quality_grade="research",
        d1=one_year_ago,
        geo=True,
        geoprivacy="open",
        per_page=200,
        page=page
    )
    results = resp.get("results", [])
    if not results:
        break
        
    for obs in results:
        geojson = obs.get("geojson")
        if geojson and "coordinates" in geojson:
            lon, lat = geojson["coordinates"]
            taxon = obs.get("taxon") or {}
            records.append({
                "id": obs["id"],
                "scientific_name": taxon.get("name", "Unknown"),
                "latitude": lat,
                "longitude": lon
            })
    time.sleep(0.5)

df = pd.DataFrame(records).dropna(subset=["latitude", "longitude"])
print(f"Loaded {len(df):,} observations.")

# Categorize species
inv_regex = "|".join(TEXAS_INVASIVES)
sgcn_regex = "|".join(TEXAS_SGCN)
df["is_invasive"] = df["scientific_name"].str.contains(inv_regex, case=False, na=False)
df["is_sgcn"] = df["scientific_name"].str.contains(sgcn_regex, case=False, na=False)

# H3 binning
df["h3_cell"] = df.apply(lambda r: h3.latlng_to_cell(r["latitude"], r["longitude"], H3_RESOLUTION), axis=1)

hex_summary = df.groupby("h3_cell").agg(
    total_obs=("id", "count"),
    species_richness=("scientific_name", "nunique"),
    invasive_obs=("is_invasive", "sum"),
    sgcn_obs=("is_sgcn", "sum")
).reset_index()

# Aggregated lists
inv_richness = df[df["is_invasive"]].groupby("h3_cell")["scientific_name"].agg(
    invasive_richness="nunique",
    invasive_list=lambda names: ", ".join(sorted(names.unique()))
).reset_index()

sgcn_richness = df[df["is_sgcn"]].groupby("h3_cell")["scientific_name"].agg(
    sgcn_richness="nunique",
    sgcn_list=lambda names: ", ".join(sorted(names.unique()))
).reset_index()

hex_summary = hex_summary.merge(inv_richness, on="h3_cell", how="left").merge(sgcn_richness, on="h3_cell", how="left")
hex_summary["invasive_richness"] = hex_summary["invasive_richness"].fillna(0).astype(int)
hex_summary["invasive_list"] = hex_summary["invasive_list"].fillna("None")
hex_summary["sgcn_richness"] = hex_summary["sgcn_richness"].fillna(0).astype(int)
hex_summary["sgcn_list"] = hex_summary["sgcn_list"].fillna("None")
hex_summary["is_under_surveyed"] = hex_summary["total_obs"] <= 5

def make_geojson(df_sub):
    feats = []
    for _, row in df_sub.iterrows():
        b = h3.cell_to_boundary(row["h3_cell"])
        coords = [[lng, lat] for lat, lng in b]
        coords.append(coords[0])
        feats.append({
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [coords]},
            "properties": {col: row[col] for col in df_sub.columns}
        })
    return {"type": "FeatureCollection", "features": feats}

def init_base_map():
    m = folium.Map(location=[29.4241, -98.4936], zoom_start=10, tiles=None)
    folium.TileLayer(
        tiles="https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer/tile/{z}/{y}/{x}",
        attr='Tiles courtesy of the <a href="https://usgs.gov/">U.S. Geological Survey</a>',
        name="USGS Topo Base",
        control=True
    ).add_to(m)
    return m

# --- GENERATE MAP 1: Richness & Gaps ---
m1 = init_base_map()
r_cmap = cm.linear.YlGnBu_09.scale(1, max(hex_summary["species_richness"].max(), 1))
r_cmap.caption = "Species Richness"

fg_rich = folium.FeatureGroup(name="Species Richness", show=True)
folium.GeoJson(
    make_geojson(hex_summary),
    style_function=lambda f: {"fillColor": r_cmap(f["properties"]["species_richness"]), "color": "#333", "weight": 0.8, "fillOpacity": 0.65},
    tooltip=GeoJsonTooltip(fields=["species_richness", "total_obs", "h3_cell"], aliases=["Richness:", "Obs:", "Cell:"])
).add_to(fg_rich)
fg_rich.add_to(m1)

fg_gaps = folium.FeatureGroup(name="Bio-Gaps (<= 5 Obs)", show=False)
folium.GeoJson(
    make_geojson(hex_summary[hex_summary["is_under_surveyed"]]),
    style_function=lambda f: {"fillColor": "#ff7800", "color": "#d95f02", "weight": 1.5, "fillOpacity": 0.5},
    tooltip=GeoJsonTooltip(fields=["total_obs", "species_richness", "h3_cell"], aliases=["Obs:", "Richness:", "Cell:"])
).add_to(fg_gaps)
fg_gaps.add_to(m1)

folium.LayerControl(collapsed=False).add_to(m1)
m1.save("map_richness_gaps.html")

# --- GENERATE MAP 2: Invasives & SGCN ---
m2 = init_base_map()
inv_cells = hex_summary[hex_summary["invasive_richness"] > 0]
if not inv_cells.empty:
    fg_inv = folium.FeatureGroup(name="Invasive Pressure", show=True)
    folium.GeoJson(
        make_geojson(inv_cells),
        style_function=lambda f: {"fillColor": "#e41a1c", "color": "#800026", "weight": 1.2, "fillOpacity": 0.65},
        tooltip=GeoJsonTooltip(fields=["invasive_richness", "invasive_list", "h3_cell"], aliases=["Invasives Count:", "Species:", "Cell:"])
    ).add_to(fg_inv)
    fg_inv.add_to(m2)

sgcn_cells = hex_summary[hex_summary["sgcn_richness"] > 0]
if not sgcn_cells.empty:
    fg_sgcn = folium.FeatureGroup(name="SGCN Refugia", show=True)
    folium.GeoJson(
        make_geojson(sgcn_cells),
        style_function=lambda f: {"fillColor": "#2b8cbe", "color": "#014636", "weight": 1.2, "fillOpacity": 0.65},
        tooltip=GeoJsonTooltip(fields=["sgcn_richness", "sgcn_list", "h3_cell"], aliases=["SGCN Count:", "Species:", "Cell:"])
    ).add_to(fg_sgcn)
    fg_sgcn.add_to(m2)

folium.LayerControl(collapsed=False).add_to(m2)
m2.save("map_conservation_threats.html")

print("Both maps generated successfully.")
