#KARWAN JALALI
#810303076
#Final Project Specials


import arcpy

#----------------------Getting data and inputs from user and output------------------------

input_pointlayer = arcpy.GetParameterAsText(0)
input_linelayer = arcpy.GetParameterAsText(1)
output_location = arcpy.GetParameterAsText(2)

#----------------------create temporary layer for point layer-------------------
#using arcpy.MakeFeatureLayer_management applied the changes on main layer too. So I used CopyFeatures_management
arcpy.CopyFeatures_management(input_pointlayer, "temp_pointlayer")
arcpy.CopyFeatures_management(input_linelayer, "temp_linelayer")
#----------------------add fields to temporary layer--------------------------
arcpy.AddField_management("temp_pointlayer", "x_Coords", "DOUBLE")
arcpy.AddField_management("temp_pointlayer", "y_Coords", "DOUBLE")
arcpy.AddField_management("temp_pointlayer", "line_dist", "DOUBLE")

#---------------Calculating X ,Y coordinate Fields using Add Geometry Attributes toolbox(Calculate and add field)------------
arcpy.AddGeometryAttributes_management("temp_pointlayer", "POINT_X_Y_Z_M")
#-------------------------------Copy Geometry Attributes fields to main X Y fields---------------------
arcpy.CalculateField_management("temp_pointlayer", "x_Coords","!POINT_X!","PYTHON")
arcpy.CalculateField_management("temp_pointlayer", "y_Coords","!POINT_Y!","PYTHON")
#-------------------------------Deleting generated fields with Geometry Attributes toolbox--------
dropFields = ["POINT_X"]
arcpy.DeleteField_management("temp_pointlayer", dropFields)
dropFields = ["POINT_Y"]
arcpy.DeleteField_management("temp_pointlayer", dropFields)

#-------------------------------Calculating Distance Fields using near (Analysis tool) toolbox--------------------------
arcpy.Near_analysis('temp_pointlayer', 'temp_linelayer')
#-------------------------------Copy Near tool fields to main distance fields--------------------
arcpy.CalculateField_management("temp_pointlayer", "line_dist","!NEAR_DIST!","PYTHON")
#-------------------------------Deleting generated fields with NEAR toolbox--------
dropFields = ["NEAR_DIST"]
arcpy.DeleteField_management("temp_pointlayer", dropFields)
dropFields = ["NEAR_FID"]
arcpy.DeleteField_management("temp_pointlayer", dropFields)
#-------------------Copies features from the input feature ---------------------
arcpy.CopyFeatures_management("temp_pointlayer", output_location)

# --------------------Delete temps-----------------------------------------
arcpy.Delete_management("temp_pointlayer")  

arcpy.Delete_management("temp_linelayer")  
# #------------------------test code SUCCESS message------------------------------------
arcpy.AddMessage("New point layer with fields added has been created")

