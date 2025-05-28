# Karwan Jalali
# 810303076
# Phase1 & 2 Shapefile
import math
import os
import matplotlib.pyplot as plt
import struct
import tkinter as tk
from tkinter import filedialog, messagebox
import sys



# <i  = little endian
# >i = big endian

#---------------------------------function for calculating perimeter --------------------
def distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

# --------------------------------Selecting shapefie function---------------------------------
def select_shapefile():
    while True:
        root = tk.Tk()
        root.withdraw() #hideing tk
        file_path = filedialog.askopenfilename(title="Please select a Shapefile")
        if file_path == "":
            sys.exit()
        if not file_path.endswith('.shp'):
            messagebox.showerror("Error", "Selected file is not a shapefile. Please select a .shp file.")
            continue
        break
    return file_path

# --------------------------------Opening shapefile---------------------------------


file_path = select_shapefile()
with (open(file_path, 'rb') as f):
    FileHeader = f.read(100)
    first4bytes = struct.unpack('>i', FileHeader[0:4])[0]
    FileLength = struct.unpack('>i', FileHeader[24:28])[0]
    Version = struct.unpack('<i', FileHeader[28:32])[0]
    shapetype = struct.unpack('<i', FileHeader[32:36])[0]
    X_min = struct.unpack('<d', FileHeader[36:44])[0]
    Y_min = struct.unpack('<d', FileHeader[44:52])[0]
    X_max = struct.unpack('<d', FileHeader[52:60])[0]
    Y_max = struct.unpack('<d', FileHeader[60:68])[0]
    Z_min = struct.unpack('<d', FileHeader[68:76])[0]
    Z_max = struct.unpack('<d', FileHeader[76:84])[0]
    M_min = struct.unpack('<d', FileHeader[84:92])[0]
    M_max = struct.unpack('<d', FileHeader[84:92])[0]
    xCoords = []
    yCoords = []
    zCoords = []
    if shapetype == 0:
        print('Null Shape')
        record_header = f.read(8)
        record_number = struct.unpack('>i', record_header[0:4])[0]
        content_length = struct.unpack('>i', record_header[4:8])[0]
        record_content = f.read(12)
        ShapeType = struct.unpack('<i', record_content[0:4])[0]
        print(record_number)
        print(content_length)

    elif shapetype == 1:
        print('Point')
        while True:
            record_header = f.read(8)
            if not record_header:
                break
            record_number = struct.unpack('>i', record_header[0:4])[0]
            content_length = struct.unpack('>i', record_header[4:8])[0]
            record_content = f.read(content_length * 2)
            ShapeType = struct.unpack('<i', record_content[0:4])[0]
            X = struct.unpack('<d', record_content[4:12])[0]
            Y = struct.unpack('<d', record_content[12:20])[0]
            xCoords.append(X)
            yCoords.append(Y)
        plt.figure(1)
        plt.title('points')
        plt.xlabel('x')
        plt.ylabel('y')
        plt.scatter(xCoords, yCoords)
        plt.show()

    elif shapetype == 3:
        print("PolyLine")

        while True:
            record_header = f.read(8)
            if not record_header:
                break
            record_number = struct.unpack('>i', record_header[0:4])[0]
            content_length = struct.unpack('>i', record_header[4:8])[0]
            record_content = f.read(content_length * 2)
            ShapeType = struct.unpack('<i', record_content[0:4])[0]
            Box = struct.unpack('<4d', record_content[4:36])[0]
            num_parts = struct.unpack('<i', record_content[36:40])[0]
            num_points = struct.unpack('<i', record_content[40:44])[0]
            parts = struct.unpack('<' + 'i' * num_parts, record_content[44:44 + 4 * num_parts])
            points = struct.unpack('<' + 'd' * (2 * num_points), record_content[44 + 4 * num_parts:])
            for part in range(num_parts):
                start = parts[part]
                if part + 1 < num_parts:
                    end = parts[part + 1]
                else:
                    end = num_points
                polyline_x = points[start * 2:end * 2:2]
                polyline_y = points[start * 2 + 1:end * 2:2]
                xCoords.append(polyline_x)
                yCoords.append(polyline_y)
        plt.figure()
        plt.title("PolyLine")
        plt.xlabel("X")
        plt.ylabel("Y")
        for i in range(len(xCoords)):
            plt.plot(xCoords[i], yCoords[i])
        plt.show()

    elif shapetype == 5:
        print('Polygon')
        total_perimeter = 0
        polygons = []
        while True:
            record_header = f.read(8)
            if not record_header:
                break
            record_number = struct.unpack('>i', record_header[0:4])[0]
            content_length = struct.unpack('>i', record_header[4:8])[0]
            record_content = f.read(content_length * 2)
            ShapeType = struct.unpack('<i', record_content[0:4])[0]
            Box = struct.unpack('<4d', record_content[4:36])[0]
            num_parts = struct.unpack('<i', record_content[36:40])[0]
            num_points = struct.unpack('<i', record_content[40:44])[0]
            parts = struct.unpack('<' + 'i' * num_parts, record_content[44:44 + 4 * num_parts])
            points = struct.unpack('<' + 'd' * (2 * num_points), record_content[44 + 4 * num_parts:])
            for part in range(num_parts):
                start = parts[part]
                if part + 1 < num_parts:
                    end = parts[part + 1]
                else:
                    end = num_points
                polygon_x = points[start * 2:end * 2:2]
                polygon_y = points[start * 2 + 1:end * 2:2]
                polygons.append((polygon_x, polygon_y))
                # Calculate perimeter for the current part
                part_perimeter = 0
                for i in range(len(polygon_x)):
                    x1, y1 = polygon_x[i], polygon_y[i]
                    if i + 1 < num_points:
                        x2, y2 = polygon_x[i + 1], polygon_y[i + 1]
                    else:
                        x2, y2 = polygon_x[0], polygon_y[0]
                    part_perimeter += distance(x1, y1, x2, y2)
                    print(f'{part_perimeter}')
                total_perimeter += part_perimeter
        plt.figure()
        plt.title("Polygon")
        plt.xlabel("X")
        plt.ylabel("Y")
        for x, y in polygons:
            plt.fill(x, y, alpha=0.5)
        plt.show()
        print(f'Total Perimeter: {total_perimeter}')




    elif shapetype == 8:
        print('MultiPoint')
        while True:
            record_header = f.read(8)
            if not record_header:
                break
            record_number = struct.unpack('>i', record_header[0:4])[0]
            content_length = struct.unpack('>i', record_header[4:8])[0]
            record_content = f.read(content_length * 2)
            ShapeType = struct.unpack('<i', record_content[0:4])[0]
            Box = struct.unpack('<4d', record_content[4:36])[0]
            Num_Points = struct.unpack('<i', record_content[36:40])[0]
            points = struct.unpack('<' + 'd' * (2 * Num_Points), record_content[40:40 + 16 * Num_Points])
            for i in range(Num_Points):
                xCoords.append(points[2 * i])
                yCoords.append(points[2 * i + 1])
        plt.figure()
        plt.title("MultiPoint")
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.scatter(xCoords, yCoords)
        plt.show()

    elif shapetype == 11:
        print('PointZ')
        xCoords = []
        yCoords = []
        zCoords = []
        Measures = []
        while True:
            record_header = f.read(8)
            if not record_header:
                break
            record_number = struct.unpack('>i', record_header[0:4])[0]
            content_length = struct.unpack('>i', record_header[4:8])[0]
            record_content = f.read(content_length * 2)
            ShapeType = struct.unpack('<i', record_content[0:4])[0]
            X = struct.unpack('<d', record_content[4:12])[0]
            Y = struct.unpack('<d', record_content[12:20])[0]
            Z = struct.unpack('<d', record_content[20:28])[0]
            Measure = struct.unpack('<d', record_content[28:36])[0]
            xCoords.append(X)
            yCoords.append(Y)
            zCoords.append(Z)
            Measures.append(Measure)
        plt.figure()
        plt.title("PointZ (XY projection with Z as color)")
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.scatter(xCoords, yCoords, c=zCoords, cmap='viridis')
        plt.colorbar(label="Z Value")
        plt.show()


    elif shapetype == 13:
        print('PolyLineZ')
        polyline_z = []
        while True:
            record_header = f.read(8)
            if not record_header:
                break
            record_number = struct.unpack('>i', record_header[0:4])[0]
            content_length = struct.unpack('>i', record_header[4:8])[0]
            record_content = f.read(content_length * 2)
            ShapeType = struct.unpack('<i', record_content[0:4])[0]
            num_parts = struct.unpack('<i', record_content[36:40])[0]
            num_points = struct.unpack('<i', record_content[40:44])[0]
            X = 44 + 4 * num_parts
            Y = X + 16 * num_points
            Z = Y + 16 + 8 * num_points
            parts = struct.unpack('<' + 'i' * num_parts, record_content[44:X])
            points = struct.unpack('<' + 'd' * (2 * num_points), record_content[X:Y])
            Zmin = struct.unpack('<d', record_content[Y:Y + 8])[0]
            Zmax = struct.unpack('<d', record_content[Y + 8:Y + 16])[0]
            Zarray = struct.unpack('<' + 'd' * num_points, record_content[Y + 16:Z])
            Mmin = struct.unpack('<d', record_content[Z:Z + 8])[0]
            Mmax = struct.unpack('<d', record_content[Z + 8:Z + 16])[0]
            Marray = struct.unpack('<' + 'd' * num_points, record_content[Z + 16:])
            for part in range(num_parts):
                start = parts[part]
                if part + 1 < num_parts:
                    end = parts[part + 1]
                else:
                    end = num_points

                polyline_z.append({
                    'x': points[start * 2:end * 2:2],
                    'y': points[start * 2 + 1:end * 2:2],
                    'z': Zarray[start:end],
                    'm': Marray[start:end]
                })
            plt.figure()
            plt.title("PolyLineZ (XY projection with Z as color)")
            plt.xlabel("X")
            plt.ylabel("Y")
            for line in polyline_z:
                plt.plot(line['x'], line['y'], color='blue', alpha=0.7)
                plt.scatter(line['x'], line['y'], c=line['z'], cmap='viridis', edgecolor='k')
            plt.colorbar(label="Z Value")
            plt.show()

    elif shapetype == 15:
        print('PolygonZ')
        polygons_z = []
        while True:
            record_header = f.read(8)
            if not record_header:
                break
            record_number = struct.unpack('>i', record_header[0:4])[0]
            content_length = struct.unpack('>i', record_header[4:8])[0]
            record_content = f.read(content_length * 2)
            ShapeType = struct.unpack('<i', record_content[0:4])[0]
            num_parts = struct.unpack('<i', record_content[36:40])[0]
            num_points = struct.unpack('<i', record_content[40:44])[0]
            X = 44 + 4 * num_parts
            Y = X + 16 * num_points
            Z = Y + 16 + 8 * num_points
            parts = struct.unpack('<' + 'i' * num_parts, record_content[44:X])
            points = struct.unpack('<' + 'd' * (2 * num_points), record_content[X:Y])
            Zmin = struct.unpack('<d', record_content[Y:Y + 8])[0]
            Zmax = struct.unpack('<d', record_content[Y + 8:Y + 16])[0]
            Zarray = struct.unpack('<' + 'd' * num_points, record_content[Y + 16:Z])
            Mmin = struct.unpack('<d', record_content[Z:Z + 8])[0]
            Mmax = struct.unpack('<d', record_content[Z + 8:Z + 16])[0]
            Marray = struct.unpack('<' + 'd' * num_points, record_content[Z + 16:])
            for part in range(num_parts):
                start = parts[part]
                if part + 1 < num_parts:
                    end = parts[part + 1]
                else:
                    end = num_points
                polygons_z.append({
                    'x': points[start * 2:end * 2:2],
                    'y': points[start * 2 + 1:end * 2:2],
                    'z': Zarray[start:end],
                    'm': Marray[start:end]
                })

            plt.figure()
            plt.title("PolygonZ (XY projection with Z as color)")
            plt.xlabel("X")
            plt.ylabel("Y")
            for polygon in polygons_z:
                plt.fill(polygon['x'], polygon['y'], alpha=0.5)
                plt.scatter(polygon['x'], polygon['y'], c=polygon['z'], cmap='viridis', edgecolor='k')
            plt.colorbar(label="Z Value")
            plt.show()


    elif shapetype == 18:
        print('MultiPointZ')
        xCoords = []
        yCoords = []
        z_values = []
        m_values = []

        while True:
            record_header = f.read(8)
            if not record_header:
                break
            record_number = struct.unpack('>i', record_header[0:4])[0]
            content_length = struct.unpack('>i', record_header[4:8])[0]
            record_content = f.read(content_length * 2)
            ShapeType = struct.unpack('<i', record_content[0:4])[0]
            Box = struct.unpack('<4d', record_content[4:36])  # Xmin, Ymin, Xmax, Ymax
            num_points = struct.unpack('<i', record_content[36:40])[0]
            X = 40 + (16 * num_points)
            points = struct.unpack('<' + 'd' * (2 * num_points), record_content[40:X])
            for i in range(num_points):
                xCoords.append(points[2 * i])
                yCoords.append(points[2 * i + 1])
            Zmin = struct.unpack('<d', record_content[X:X + 8])[0]
            Zmax = struct.unpack('<d', record_content[X + 8:X + 16])[0]
            Y = X + 16 + (8 * num_points)
            Zarray = struct.unpack('<' + 'd' * num_points, record_content[X + 16:Y])
            z_values.extend(Zarray)
            Mmin = struct.unpack('<d', record_content[Y:Y + 8])[0]
            Mmax = struct.unpack('<d', record_content[Y + 8:Y + 16])[0]
            Marray = struct.unpack('<' + 'd' * num_points, record_content[Y + 16:])
            m_values.extend(Marray)
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.scatter(xCoords, yCoords, z_values, c='b', marker='o')
        ax.set_xlabel('X Coordinate')
        ax.set_ylabel('Y Coordinate')
        ax.set_zlabel('Z Value')
        ax.set_title('MultiPointZ Plot')
        plt.show()

    elif shapetype == 21:
        import numpy as np

        print('PointM')
        PointM = []
        while True:
            record_header = f.read(8)
            if not record_header:
                break
            record_number = struct.unpack('>i', record_header[0:4])[0]
            content_length = struct.unpack('>i', record_header[4:8])[0]
            record_content = f.read(content_length * 2)
            ShapeType = struct.unpack('<i', record_content[0:4])[0]
            X = struct.unpack('<d', record_content[4:12])[0]
            Y = struct.unpack('<d', record_content[12:20])[0]
            M = struct.unpack('<d', record_content[20:])[0]
            PointM.append({
                'x': X,
                'y': Y,
                'm': M if M >= 0 and not np.isnan(M) else 0
            })
        plt.figure()
        x_vals = [point['x'] for point in PointM]
        y_vals = [point['y'] for point in PointM]
        m_vals = [point['m'] for point in PointM]
        scatter = plt.scatter(x_vals, y_vals, c=m_vals, cmap='viridis', edgecolor='k', alpha=0.7)
        plt.colorbar(scatter, label="M Value")
        plt.title("PointM (XY projection with M as color)")
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.show()

    elif shapetype == 23:
        import numpy as np

        print('PolyLineM')
        polyline_M = []
        while True:
            record_header = f.read(8)
            if not record_header:
                break
            record_number = struct.unpack('>i', record_header[0:4])[0]
            content_length = struct.unpack('>i', record_header[4:8])[0]
            record_content = f.read(content_length * 2)
            ShapeType = struct.unpack('<i', record_content[0:4])[0]
            Box = struct.unpack('<4d', record_content[4:36])
            num_parts = struct.unpack('<i', record_content[36:40])[0]
            num_points = struct.unpack('<i', record_content[40:44])[0]
            X = 44 + (4 * num_parts)
            Y = X + (16 * num_points)
            parts = struct.unpack('<' + 'i' * num_parts, record_content[44:X])
            points = struct.unpack('<' + 'd' * (2 * num_points), record_content[X:Y])
            Mmin = struct.unpack('<d', record_content[Y:Y + 8])
            Mmax = struct.unpack('<d', record_content[Y + 8:Y + 16])
            Marray = list(struct.unpack('<' + 'd' * num_points, record_content[Y + 16:]))
            for part in range(num_parts):
                start = parts[part]
                end = parts[part + 1] if part + 1 < num_parts else num_points
                polyline_M.append({
                    'x': points[start * 2:end * 2:2],
                    'y': points[start * 2 + 1:end * 2:2],
                    'm': [m if m >= 0 and not np.isnan(m) else 0 for m in Marray[start:end]]
                })
        plt.figure()
        plt.title("PolyLineM (XY projection with M as color)")
        plt.xlabel("X")
        plt.ylabel("Y")
        for line in polyline_M:
            plt.plot(line['x'], line['y'], color='blue', alpha=0.7)
            scatter = plt.scatter(line['x'], line['y'], c=line['m'], cmap='viridis', edgecolor='k')
        plt.colorbar(scatter, label="M Value")
        plt.show()

    elif shapetype == 25:
        import numpy as np

        print('PolygonM')
        polygon_M = []
        while True:
            record_header = f.read(8)
            if not record_header:
                break
            record_number = struct.unpack('>i', record_header[0:4])[0]
            content_length = struct.unpack('>i', record_header[4:8])[0]
            record_content = f.read(content_length * 2)
            ShapeType = struct.unpack('<i', record_content[0:4])[0]
            Box = struct.unpack('<4d', record_content[4:36])
            num_parts = struct.unpack('<i', record_content[36:40])[0]
            num_points = struct.unpack('<i', record_content[40:44])[0]
            X = 44 + (4 * num_parts)
            Y = X + (16 * num_points)
            parts = struct.unpack('<' + 'i' * num_parts, record_content[44:X])
            points = struct.unpack('<' + 'd' * (2 * num_points), record_content[X:Y])
            Mmin = struct.unpack('<d', record_content[Y:Y + 8])
            Mmax = struct.unpack('<d', record_content[Y + 8:Y + 16])
            Marray = list(struct.unpack('<' + 'd' * num_points, record_content[Y + 16:]))

            for part in range(num_parts):
                start = parts[part]
                if part + 1 < num_parts:
                    end = parts[part + 1]
                else:
                    end = num_points
                polygon_M.append({
                    'x': points[start * 2:end * 2:2],
                    'y': points[start * 2 + 1:end * 2:2],
                    'm': [m if m >= 0 and not np.isnan(m) else 0 for m in Marray[start:end]]
                })
        plt.figure(figsize=(10, 8))
        plt.title("PolygonM (XY projection with M as color)")
        plt.xlabel("X")
        plt.ylabel("Y")
        for polygon in polygon_M:
            plt.fill(polygon['x'], polygon['y'], color='blue', alpha=0.3)
            scatter = plt.scatter(polygon['x'], polygon['y'], c=polygon['m'], cmap='viridis', edgecolor='k')
        plt.colorbar(scatter, label="M Value")
        plt.show()


    elif shapetype == 28:
        import numpy as np

        print('MultiPointM')
        MultiPointM = []
        while True:
            record_header = f.read(8)
            if not record_header:
                break
            record_number = struct.unpack('>i', record_header[0:4])[0]
            content_length = struct.unpack('>i', record_header[4:8])[0]
            record_content = f.read(content_length * 2)
            ShapeType = struct.unpack('<i', record_content[0:4])[0]
            Box = struct.unpack('<4d', record_content[4:36])
            num_points = struct.unpack('<i', record_content[36:40])[0]
            X = 40 + (16 * num_points)
            points = struct.unpack('<' + 'd' * (2 * num_points), record_content[40:X])
            xCoords = points[0::2]
            yCoords = points[1::2]
            m_range_start = X
            Mmin = struct.unpack('<d', record_content[X: X + 8])
            Mmax = struct.unpack('<d', record_content[X + 8:X + 16])
            m_values = list(struct.unpack('<' + 'd' * num_points, record_content[X + 16:]))
            for i in range(num_points):
                MultiPointM.append({
                    'x': xCoords[i],
                    'y': yCoords[i],
                    'm': m_values[i] if m_values[i] >= 0 and not np.isnan(m_values[i]) else 0
                })
        plt.figure()
        x_vals = [point['x'] for point in MultiPointM]
        y_vals = [point['y'] for point in MultiPointM]
        m_vals = [point['m'] for point in MultiPointM]
        scatter = plt.scatter(x_vals, y_vals, c=m_vals, cmap='viridis', edgecolor='k', alpha=0.7)
        plt.colorbar(scatter, label="M Value")
        plt.title("MultiPointM (XY projection with M as color)")
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.show()

    elif shapetype == 31:
        print('MultiPatch')



#---------------------------Phase 2----------------------------------------------






#---------------------------Applying transformation function---------------------
def transformationFunction(x, y, action):
    if action == "rotate":
        #----------------Rotating around bounding box center------------------------
        X0 = (X_min + X_max) / 2
        Y0 = (Y_min + Y_max) / 2
        #-----------------------Rotation counterclockwise matrix elements ----------
        x_new = X0 + (x - X0) * math.cos(angle_rad) - (y - Y0) * math.sin(angle_rad)
        y_new = Y0 + (x - X0) * math.sin(angle_rad) + (y - Y0) * math.cos(angle_rad)
        return x_new, y_new
    # ----------------Applying shift on coordinates------------------------
    elif action == "shift":
        return x + shift_x, y + shift_y
    else:
        raise ValueError("Invalid action. Please choose 'rotate' or 'shift'.")

if shapetype == 1 or shapetype == 3 or shapetype == 5:
    # -------------------get transformation parameters-------------------------
    while True:
        message='Do you want to perform a transformation? (yes to continue/any key to quit): '
        Choice = input(message).strip().lower()
        if Choice =='yes':
            break
        else:
            print("Program terminated.")
            sys.exit()

    while True:
        action = input("Choose transformation: rotate or shift?(or exit) ").strip().lower()
        if action in ["rotate", "shift"]:
            break
        elif action=='exit':
            print("Program terminated.")
            sys.exit()
        else:
            print("Invalid input. Please enter 'rotate' or 'shift'.")

    if action == "rotate":
        while True:
            try:
                angle = float(input("Enter rotation angle in degrees: "))
                angle_rad = math.radians(angle)
                break
            except ValueError:
                print("Invalid input. Please enter a valid number for the angle.")

    elif action == "shift":
        while True:
            try:
                shift_x = float(input("Enter shift in X direction: "))
                shift_y = float(input("Enter shift in Y direction: "))
                break
            except ValueError:
                print("Invalid input. Please enter valid numbers for the shifts.")

    # -------------------setting output path and file extension-------------------------
    output_path = os.path.splitext(file_path)[0] + "_transformed.shp"
    # ----------------reading and writing the file-------------------------------------
    with (open(file_path, 'rb') as f, open(output_path, 'wb') as f_out):
        # ----------------reading and writing file header-------------------------------------
        FileHeader = f.read(100)
        f_out.write(FileHeader)
        #----------------reading and writing point shapefile-----------------------
        if shapetype == 1:  # Point
            while True:
                # ----------------reading and writing record header without change--------------
                record_header = f.read(8)
                if not record_header:
                    break
                f_out.write(record_header)
                # ----------------reading record content applying changes and writing it--------
                record_content = f.read(content_length * 2)
                ShapeType = struct.unpack('<i', record_content[0:4])[0]
                X = struct.unpack('<d', record_content[4:12])[0]
                Y = struct.unpack('<d', record_content[12:20])[0]
                X_new, Y_new = transformationFunction(X, Y, action)
                #----------------record_content[:4] shapeType without changes------------------
                record_content = record_content[:4] + struct.pack('<2d', X_new, Y_new)
                f_out.write(record_content)
            print(f"Transformed shapefile saved at: {output_path}")
        #----------------reading and writing PolyLine,Polygon shapefile-----------------------
        elif shapetype == 3 or shapetype == 5:
            while True:
                record_header = f.read(8)
                if not record_header:
                    break
                f_out.write(record_header)
                record_content = f.read(content_length * 2)
                num_parts = struct.unpack('<i', record_content[36:40])[0]
                num_points = struct.unpack('<i', record_content[40:44])[0]
                parts = struct.unpack('<' + 'i' * num_parts, record_content[44:44 + 4 * num_parts])
                points = struct.unpack('<' + '2d' * num_points, record_content[44 + 4 * num_parts:])
                # ----------------applying transformation function on points-----------------------
                transformed_points = []
                for i in range(num_points):
                    x = points[2 * i]
                    y = points[2 * i + 1]
                    x_new, y_new = transformationFunction(x, y, action)
                    transformed_points.extend([x_new, y_new])
                # ----------------writing record contents(transformed points)------------------------
                record_content = (
                        record_content[:44 + 4 * num_parts] +  #writing constant part of record content
                        struct.pack('<' + '2d' * num_points, *transformed_points)
                )
                f_out.write(record_content)
            print(f"Transformed shapefile saved at: {output_path}")







