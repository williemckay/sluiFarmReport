import arcpy
import shutil
import os
import pandas as pd
import pyodbc
import numpy as np
import datetime

gdb = r"\\gisdata\gis\Department\Environmental_Management\SLUI\ArcPro_Projects\FarmWorksReports\FarmWorksReports.gdb"

#Set the arcpy EnvironmentSettings
arcpy.env.overwriteOutput=True
arcpy.env.transferDomains = True

#Clear the cache
arcpy.management.ClearWorkspaceCache()

#define the map
aprx = arcpy.mp.ArcGISProject(r"\\gisdata\GIS\Department\Environmental_Management\SLUI\ArcPro_Projects\FarmWorksReports\FarmWorksReports_31.aprx")
m = aprx.listMaps("Map")#[0]


# Take copies of feature classes from SLUI
arcpy.FeatureClassToFeatureClass_conversion(
    r"SLUI Work Polygons", 
    gdb, 
    "SLUIWorkPolysExported"
    )

arcpy.FeatureClassToFeatureClass_conversion(
    r"SLUI Work Lines", 
    gdb, 
    "SLUIWorkLinesExported"
    )

arcpy.FeatureClassToFeatureClass_conversion(
    r"SLUI LUC", 
    gdb, 
    "SLUIlucExported"
    )


#Update geometry
arcpy.CalculateField_management(
    'SLUIWorkPolysExported', 
    'Hectares', 
    '!shape.area@hectares!', 
    'PYTHON_9.3', 
    '#'
    )

arcpy.CalculateField_management(
    'SLUIlucExported', 
    'Hectares', 
    '!shape.area@hectares!', 
    'PYTHON_9.3', 
    '#'
    )

arcpy.CalculateField_management(
    'SLUIWorkLinesExported', 
    'Meters', 
    '!shape.area@meters!', 
    'PYTHON_9.3', 
    '#'
    )


# Dissolve and Classify records 
arcpy.management.SelectLayerByAttribute(
    in_layer_or_view="SLUIlucExported",
    selection_type="NEW_SELECTION",
    where_clause="Cov10TH IS NULL",
    invert_where_clause=None
)

arcpy.management.CalculateField(
    in_table="SLUIlucExported",
    field="Cov10TH",
    expression="0",
    expression_type="PYTHON3",
    code_block="",
    field_type="TEXT",
    enforce_domains="NO_ENFORCE_DOMAINS"
)

arcpy.management.SelectLayerByAttribute(
    in_layer_or_view="SLUIlucExported",
    selection_type="CLEAR_SELECTION",
    where_clause="",
    invert_where_clause=None
)

arcpy.management.CalculateField(
    "SLUIlucExported", 
    "Cover", 
    "reclass(!Cov10TH!)", 
    "PYTHON3", 
    """def reclass(cov):
        if cov >=6:
            return 'Trees'
        else:
            return 'Pasture'""", 
    "TEXT",
    "NO_ENFORCE_DOMAINS"
    )

arcpy.management.Dissolve(
    "SLUIlucExported", 
    r"\\gisdata\gis\Department\Environmental_Management\SLUI\ArcPro_Projects\FarmWorksReports\FarmWorksReports.gdb\SLUIlucExported_Dissolve", 
    "HEL_Class;Cover", 
    "Hectares SUM", 
    "MULTI_PART", 
    "DISSOLVE_LINES"
    )