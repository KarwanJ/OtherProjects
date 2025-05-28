#group8
#---------------------Karwan Jalali & Farshad Shamsikhani-----------------------

#------------------------Importing the libraries and reading the file----------------------
import os
import geopandas as gpd  #work with spatial data
from shapely.geometry import Point, LineString   #work with shapefiles
import matplotlib  #plot
import matplotlib.pyplot as plt
import networkx as nx  #creating graph
matplotlib.use('TkAgg') #matplot lib backend for showing plots

# reading shapefile using geopandas
roads = gpd.read_file("layers/roads.shp")

# Check if the 'export' folder exists, if not, create it
if not os.path.exists('Exports'):
    os.makedirs('Exports')

#------------------------Creating graph--------------------------------
# creating empty graph using networkx
roads_graph = nx.Graph()
# Loop over all rows of ((roads dataframe)) with iterrows from pandas for filling the graph
# each dataframe has indices and rows. rows has many columns include geometry
for index, row in roads.iterrows():
    line = row.geometry  #creating linestring includes x,y coordinates as tuples for each line
    coords = list(line.coords) #creating list of coordinates
    for j in range(len(coords) - 1):
        u = coords[j]  #first node of each line
        v = coords[j + 1] #last node of each line
        length = Point(u).distance(Point(v)) #calculating length using distance function from shaply library
        roads_graph.add_edge(u, v, weight=length) #adding each edge to the graph



#-------------------getting the points from the user---------------------------
# function to find the nearest node of where the user clicked
def find_nearest_node(point, nodes):
    nearest_node = None
    min_dist = float('inf')
    for node in nodes: #loop over all nodes to find the nearest node
        dist = Point(node).distance(point)
        if dist < min_dist:
            min_dist = dist
            nearest_node = node
    return nearest_node

#empty list for saving clicks
clicks = []

#Function for Receiving two clicks from the user to select start and goal points
def getpointbyclick(event):
    if event.xdata is not None and event.ydata is not None:
        clicks.append(Point(event.xdata, event.ydata))#list of x,y tuples
        print(f"📍 selected point: ({event.xdata:.2f}, {event.ydata:.2f})")

        # Draw a red circle at the selected point
        ax.plot(event.xdata, event.ydata, 'ro')  # 'ro' means red circle marker
        plt.draw()  # Redraw the plot to display the circle

        if len(clicks) == 2:
            plt.close()

fig, ax = plt.subplots(figsize=(8, 6))
roads.plot(ax=ax, color='#FFCC99')
plt.title("Specify Start and Goal points")
#connecting click function to click event in figure window
click_event_id = fig.canvas.mpl_connect('button_press_event', getpointbyclick)
plt.show()

if len(clicks) < 2:
    print("Two points not selected! The program stopped.")
    exit()

# Getting the closest nodes to selected points using find_nearest_node function
start = find_nearest_node(clicks[0], roads_graph.nodes)
goal = find_nearest_node(clicks[1], roads_graph.nodes)






#------------------------Implementation of A* algorithm---------------------------

#Definition of a heuristic function to calculate the Euclidean distance from the current node to the goal node
def h(n):
    return Point(n).distance(Point(goal))
def f(n):
    return g[n] + h(n)
#g[n] is the value for node n from the g dictionary
#A* algorithm According to the PSEUDO CODE
open_list = [start] #List of nodes that need to be evaluated
closed_list = [] #LList of nodes that have already been evaluated
g = {start: 0} #Dictionary storing the cost to reach each node (g(n)). key:node value:cost
previous_nodes = {} #dictionary contain nodes as keys parents as values

while open_list:
    # current node coords is node which f(n) is min
    current = min(open_list, key=f)  #apply f function on all nodes in open_list
    if current == goal:
        path = []
        #creating the path from end to begining
        while current in previous_nodes:
            path.append(current)
            current = previous_nodes[current]
        path.append(start)
        path.reverse()
        break
    open_list.remove(current)
    closed_list.append(current)


    for neighbor in roads_graph.neighbors(current): #loop over all neighbours of current neighbour using networkx.neighbors library
        cost = roads_graph[current][neighbor]['weight'] #returning the cost between current and all neighbours
        new_g = g[current] + cost #calculating new g(n)
        # Get the cost of reaching the neighbor node, default to infinity if it's not found
        neighbor_cost = g.get(neighbor, float('inf'))
        # Check if the neighbor is in open_list and the new path is worse or equal
        if neighbor in open_list and new_g >= neighbor_cost:
            continue
        # Check if the neighbor is in closed_list and the new path is worse or equal
        if neighbor in closed_list and new_g >= neighbor_cost:
            continue
        # If the neighbor is in open_list, remove it for reevaluation
        if neighbor in open_list:
            open_list.remove(neighbor)
        # If the neighbor is in closed_list, remove it for reevaluation
        if neighbor in closed_list:
            closed_list.remove(neighbor)
        previous_nodes[neighbor] = current #Set the current node as the parent of the neighbor
        g[neighbor] = new_g # add the neighbor to the open_list to evaluate it later
        open_list.append(neighbor) #Add the neighbor to the open_list to evaluate it later
else:
    print("No path found.")
    exit()




#--------------------------creating the Linestrings------------------------------
#create linestrings from path(list of nodes)
lines = []
for i in range(len(path) - 1):
    lines.append(LineString([path[i], path[i + 1]]))

#creating shape file
shortest_path = gpd.GeoDataFrame(geometry=lines, crs=roads.crs)
shortest_path.to_file("Exports/shortest_path.shp")

#calculating length
total_length = sum(line.length for line in lines)
print(f"Shortest path: {total_length:.2f} meters")






#------------------------Plottings shapefiles----------------------------
fig, ax = plt.subplots(figsize=(8, 6))
roads.plot(ax=ax, color='#FFCC99', linewidth=0.7, label='Roads')
shortest_path.plot(ax=ax, color='red', linewidth=2, label='Shortest Path')
gpd.GeoSeries(clicks).plot(ax=ax, color='blue', markersize=80, label='Start / Goal')

plt.title("Shortest path with A* algorithm")
plt.legend()


plt.text(
    x=0.01, y=0.01,  # Position the text at 1% from the left and 1% from the bottom of the axis
    s=f"path length: {total_length:.2f} meters",  # The text to display, including the formatted total path length
    transform=ax.transAxes,  # Set the coordinate system to relative axis coordinates (0 to 1 range)
    fontsize=12,  # Set the font size of the text
    color="black",  # Set the text color to black
    bbox=dict(facecolor='white', edgecolor='gray', boxstyle='round,pad=0.5')  # Add a white background box with rounded corners
)
plt.axis('off')
plt.tight_layout() # Adjust the paddings
plt.savefig("Exports/shortest_path_map.png", dpi=300)
plt.show()



