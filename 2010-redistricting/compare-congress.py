import geopandas as gpd
from geopandas import GeoSeries
import fiona
from fiona.crs import from_epsg
import shapely
from shapely.geometry import shape
from shapely.ops import cascaded_union
from shapely.geometry import Polygon
from shapely.geometry import MultiPolygon
import matplotlib.pyplot as plt
import warnings
warnings.simplefilter("ignore")


census2010shp = gpd.read_file("Tract_2010Census_DP1/Tract_2010Census_DP1.shp")
total_population = sum(census2010shp['DP0030001']);
print("Total 16+ population: " + str(total_population))


cong2010shp = gpd.read_file("tl_2010_us_cd108/tl_2010_us_cd108.shp")
cong2010 = {}
for index, poi in cong2010shp.iterrows():
	district = cong2010shp.loc[index]
	#print(district["STATEFP00"]+"_"+district["CD108FP"]);
	cong2010[district["STATEFP00"]+"_"+district["CD108FP"]] = district

cong2014shp = gpd.read_file("tl_2014_us_cd114/tl_2014_us_cd114.shp")
cong2014 = {}
for index, poi in cong2014shp.iterrows():
	district = cong2014shp.loc[index]
	#print(district["STATEFP"]+"_"+district["CD114FP"]);
	cong2014[district["STATEFP"]+"_"+district["CD114FP"]] = district

global_diffs = []
for key, value in cong2014.items() :
	#print("Comparing congressional district ",key,"...")
	if key not in cong2010:
		# cong2014[key] is a new district entirely... add it to union
		diff = shape(cong2014[key]["geometry"])
		if type(diff) is Polygon:
			diff = shapely.geometry.MultiPolygon([shapely.wkt.loads(str(diff))])
		global_diffs.append(diff)
	else: # key is in both... see if it changed
		district2010 = shape(cong2010[key]["geometry"])
		district2014 = shape(cong2014[key]["geometry"])
		diff = district2010.difference(district2014)
		if type(diff) is Polygon:
			diff = shapely.geometry.MultiPolygon([shapely.wkt.loads(str(diff))])
		global_diffs.append(diff)

#print(gpd.GeoSeries(global_diffs).to_json()) # uncomment this to dump out GeoJSON

changed = gpd.GeoSeries(global_diffs)


def area_overlaps(gm, gs):
	area = 0
	for i in range(len(gs)):
		if gm.intersects(gs[i]):
			area = area + gm.intersection(gs[i]).area
	return area


def completely_contains(gm, gs):
	for i in range(len(gs)):
		if gs[i].contains(gm):
			return 1
	return 0


census2010shp['area_overlaps'] = census2010shp['geometry'].apply(lambda shp: area_overlaps(shp, changed))
census2010shp['overlaps'] = census2010shp['area_overlaps'].apply(lambda x: 1 if x > 0 else 0)
census2010shp['contains'] = census2010shp['geometry'].apply(lambda shp: completely_contains(shp, changed))

overlaps_method_tracts = sum(census2010shp['overlaps'])
contains_method_tracts = sum(census2010shp['contains'])
overlaps_method_population = sum(census2010shp['DP0030001'] * census2010shp['overlaps'])
contains_method_population = sum(census2010shp['DP0030001'] * census2010shp['contains'])
area_proportional_overlap_method_population = sum(census2010shp['DP0030001'] * census2010shp['area_overlaps'] / census2010shp['geometry'].area)

print( "Affected 16+ population (Overlaps method): " + str(overlaps_method_population) + " (" + str(round(100 * overlaps_method_population / total_population)) + "%)" )
print( "(" + str(overlaps_method_tracts) + " tracts)" )
print( "Affected 16+ population (Contains method): " + str(contains_method_population) + " (" + str(round(100 * contains_method_population / total_population)) + "%)" )
print( "(" + str(contains_method_tracts) + " tracts)" )
print( "Affected 16+ population (Area-Proportional Overlap method): " + str(area_proportional_overlap_method_population) +
	" (" + str(round(100 * area_proportional_overlap_method_population / total_population)) + "%)" )

#changed.plot()
#plt.show()
#census2010shp.loc[census2010shp['overlaps']==1].plot()
#plt.show()
#census2010shp.loc[census2010shp['contains']==1].plot()
#plt.show()
