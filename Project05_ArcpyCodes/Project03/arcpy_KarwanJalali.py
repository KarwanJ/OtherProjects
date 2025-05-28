#KARWAN JALALI
#810303076
#Project 5


import arcpy

#----------------------Getting data and inputs from user--------------------

input_feature = arcpy.GetParameterAsText(0)

output_location = arcpy.GetParameterAsText(1)
#----------------------create temporary layer-------------------------------
arcpy.MakeFeatureLayer_management(input_feature, "input_temp")
# #----------------------Selecting all points from temporary layer------------
arcpy.SelectLayerByAttribute_management("input_temp", "NEW_SELECTION")
#----------------------Creating converxhull from all points------------------
arcpy.MinimumBoundingGeometry_management("input_temp",output_location,"CONVEX_HULL", "ALL")
