#KARWAN JALALI
#810303076

import arcpy

#----------------------Getting data and inputs from user--------------------

input_points1 = arcpy.GetParameterAsText(0)
input_points2 = arcpy.GetParameterAsText(1)
buffer_Distance = arcpy.GetParameterAsText(2)
output_location = arcpy.GetParameterAsText(3)

#----------------------create temporary layer--------------------
arcpy.MakeFeatureLayer_management(input_points1, "temp_input_points1")
arcpy.MakeFeatureLayer_management(input_points2, "temp_input_points2")


#---------------------Buffer ------------------------------------------
arcpy.Buffer_analysis("temp_input_points1", "temp_buffer1", buffer_Distance)
arcpy.Buffer_analysis("temp_input_points2", "temp_buffer2",buffer_Distance)

# # --------------------- create buffer overlap ---------------------------------
arcpy.Intersect_analysis(["temp_buffer1", "temp_buffer2"], "OverlapPolygon")

#--------------------------- make a polygon outline----------------------------

arcpy.CopyFeatures_management("OverlapPolygon", output_location)

# --------------------Delete temp_buffer-----------------------------------------
arcpy.Delete_management("temp_buffer1")
arcpy.Delete_management("temp_buffer2")
arcpy.Delete_management("OverlapPolygon") 

# #------------------------test code SUCCESS message------------------------------------
arcpy.AddMessage("Task has been finished")