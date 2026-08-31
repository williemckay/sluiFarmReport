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
    os.path.join(gdb, "SLUIlucExported_Dissolve"), 
    "HEL_Class;Cover", 
    "Hectares SUM", 
    "MULTI_PART", 
    "DISSOLVE_LINES"
    )

arcpy.management.Dissolve(
    "SLUIWorkPolysExported", 
    os.path.join(gdb, "SLUIWorkPolysExported_Dissolve"), 
    "job_type", 
    [["Hectares", "SUM"], ["num_plant", "SUM"]],
    "MULTI_PART", 
    "DISSOLVE_LINES"
    )

arcpy.management.Dissolve(
    "SLUIWorkLinesExported", 
    os.path.join(gdb, "SLUIWorkLinesExported_Dissolve"), 
    "job_type", 
    "Perimeter SUM", 
    "MULTI_PART", 
    "DISSOLVE_LINES"
    )

#reclassify jobtypes
arcpy.management.AddField(
    "SLUIWorkPolysExported",
    "jobtype_reclass",
    "TEXT",
    field_length=50
)

arcpy.management.AddField(
    "SLUIWorkLinesExported",
    "jobtype_reclass",
    "TEXT",
    field_length=50
)

reclass = {
    1: "Afforestation",
    2: "Retirement",
    3: "Riparian Retirement",
    4: "Wetland Retirement",
    5: "Managed Retirement",
    6: "Pole Planting",
    7: "Pole Planting",
    8: "Structures/Earthworks",
    9: "Other"
}

with arcpy.da.UpdateCursor(
    "SLUIWorkLinesExported",
    ["jobtype", "jobtype_reclass"]
) as cursor:

    for row in cursor:
        row[1] = reclass.get(row[0], row[0])
        cursor.updateRow(row)

with arcpy.da.UpdateCursor(
    "SLUIWorkPolysExported",
    ["jobtype", "jobtype_reclass"]
) as cursor:

    for row in cursor:
        row[1] = reclass.get(row[0], row[0])
        cursor.updateRow(row)