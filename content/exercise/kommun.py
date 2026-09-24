import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import time
from concurrent.futures import ThreadPoolExecutor


points = pd.read_csv("./municipality_se.csv",usecols=["Locality", "Municipality", "County", "Latitude", "Longitude"])
polygons = gpd.read_file("./kommun_se.geojson")

n_points = len(points)
n_polygons = len(polygons)

def check_polygon(polygon_idx):
    """Worker function to process a single polygon"""
    current_polygon = polygons.iloc[polygon_idx]["geometry"]
    out_points = []
    # manually loop over all points, check if polygon contains that point
    for i in range(n_points):
        current_point = points.iloc[i, :]
        if current_polygon.contains(Point(current_point.Longitude,current_point.Latitude)):
            out_points.append(current_point.Locality)
    return out_points

t_start=time.time()

points_per_polygon = {}

for polygon_idx in range(n_polygons):
    points_per_polygon[polygon_idx] = check_polygon(polygon_idx)

t_end=time.time()
