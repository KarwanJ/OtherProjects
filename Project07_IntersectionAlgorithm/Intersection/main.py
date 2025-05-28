# #group8
#group8
#---------------------Karwan Jalali & Farshad Shamsikhani-----------------------

import matplotlib  # Import matplotlib library for plotting
matplotlib.use('TkAgg')  # Set the backend to TkAgg for interactive plotting
import geopandas as gpd  # Import geopandas for handling geospatial data
from shapely.geometry import LineString, Point  # Import LineString and Point classes from shapely for geometry operations
import matplotlib.pyplot as plt  # Import pyplot for creating visualizations
import os  # Import os for file and directory operations

# ===========================
# Segment class to represent a line segment
# ===========================
class Segment:  # Define Segment class to store and manage line segment properties
    def __init__(self, p1, p2, id=None):  # Initialize segment with two endpoints and optional ID
        # Determine which point is the upper (higher y, or left-most if equal y)
        if p1[1] > p2[1] or (p1[1] == p2[1] and p1[0] < p2[0]):  # Compare y-coordinates, then x if y's are equal
            self.upper = p1  # Assign point with higher y as upper
            self.lower = p2  # Assign other point as lower
        else:  # If p2 has higher y or left-most when y's are equal
            self.upper = p2  # Assign p2 as upper
            self.lower = p1  # Assign p1 as lower
        self.id = id  # Store segment ID
        self.is_horizontal = abs(p1[1] - p2[1]) < 1e-5  # Check if segment is nearly horizontal by comparing y-coordinates

    def get_x_at_y(self, y):  # Method to calculate x-coordinate at a given y
        # Returns x-coordinate of the segment at a specific y (used in status ordering)
        x1, y1 = self.upper  # Get x, y of upper point
        x2, y2 = self.lower  # Get x, y of lower point
        if self.is_horizontal:  # If segment is horizontal
            return (x1 + x2) / 2  # Return midpoint x-coordinate
        if abs(y2 - y1) < 1e-6:  # If y difference is nearly zero (vertical or near-vertical)
            return x1  # Return x-coordinate of upper point
        return x1 + (x2 - x1) * (y - y1) / (y2 - y1)  # Calculate x using linear interpolation

# ===========================
# Read segments from shapefile into a list of Segment objects
# ===========================
def read_segments_from_shapefile(shapefile_path):  # Function to read line segments from a shapefile
    gdf = gpd.read_file(shapefile_path)  # Load shapefile into a GeoDataFrame
    segments = []  # Initialize list to store Segment objects
    print("Geometry types in shapefile:", gdf.geometry.type.unique())  # Print unique geometry types in shapefile
    print("Total features:", len(gdf))  # Print total number of features
    for index, row in gdf.iterrows():  # Iterate through each feature in GeoDataFrame
        line = row.geometry  # Get geometry of current feature
        if isinstance(line, LineString):  # Check if geometry is a LineString
            coords = list(line.coords)  # Get list of coordinates
            for j in range(len(coords) - 1):  # Iterate through consecutive pairs of points
                p1 = coords[j]  # First point of segment
                p2 = coords[j + 1]  # Second point of segment
                segment = Segment(p1, p2, id=f"{index}_{j}")  # Create Segment object with ID
                segments.append(segment)  # Add segment to list
        else:  # If geometry is not a LineString
            print(f"Skipping unsupported geometry at index {index}: {type(line)}")  # Print warning for unsupported geometry
    print("Total segments created:", len(segments))  # Print total number of segments created
    return segments, gdf  # Return list of segments and GeoDataFrame

# ===========================
# Event class for sweep line events (segment endpoints and intersections)
# ===========================
class Event:  # Define Event class for sweep line algorithm events
    def __init__(self, point, event_type, segments):  # Initialize event with point, type, and associated segments
        self.point = point  # Store event point as (x, y) tuple
        self.type = event_type  # Store event type ('start', 'end', or 'intersection')
        self.segments = segments  # Store list of segments involved in the event

    def __lt__(self, other):  # Define less-than comparison for sorting events
        # Events are ordered top-to-bottom, then left-to-right
        if abs(self.point[1] - other.point[1]) > 1e-6:  # Compare y-coordinates
            return self.point[1] > other.point[1]  # Higher y comes first
        return self.point[0] < other.point[0]  # If y's equal, smaller x comes first

    def __repr__(self):  # Define string representation of Event
        return f"{self.type} @ {self.point}"  # Return event type and point

# ===========================
# Event queue to manage all upcoming sweep line events
# ===========================
class EventQueue:  # Define EventQueue class to manage sweep line events
    def __init__(self):  # Initialize event queue
        self.events = []  # List to store events
        self.seen_points = set()  # Set to track seen points to avoid duplicates

    def add(self, event):  # Method to add an event to the queue
        # Avoid adding duplicate events
        point_tuple = (round(event.point[0], 8), round(event.point[1], 8))  # Round point coordinates to avoid floating-point issues
        if point_tuple not in self.seen_points:  # Check if point is not already seen
            self.events.append(event)  # Add event to list
            self.events.sort()  # Sort events to maintain order
            self.seen_points.add(point_tuple)  # Mark point as seen

    def pop(self):  # Method to remove and return the next event
        return self.events.pop(0)  # Remove and return first event

    def is_empty(self):  # Method to check if queue is empty
        return len(self.events) == 0  # Return True if no events remain

# ===========================
# Geometry helpers
# ===========================
def ccw(A, B, C):  # Function to check if points A, B, C are in counterclockwise order
    return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])  # Compute cross product

def do_intersect(s1, s2):  # Function to check if two segments intersect
    A, B = s1.upper, s1.lower  # Get endpoints of first segment
    C, D = s2.upper, s2.lower  # Get endpoints of second segment
    return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)  # Check orientation conditions for intersection

# ===========================
# Sweep line status structure to track active segments
# ===========================
class StatusStructure:  # Define StatusStructure class to manage active segments during sweep
    def __init__(self):  # Initialize status structure
        self.active_segments = []  # List to store active segments

    def insert(self, segment, y):  # Method to insert a segment into status
        # Insert segment into correct horizontal order based on x at sweep line y
        if segment.is_horizontal:  # If segment is horizontal
            self.active_segments.append(segment)  # Append to end of list
        else:  # If segment is non-horizontal
            x = segment.get_x_at_y(y - 1e-6)  # Get x-coordinate at slightly above current y
            i = 0  # Initialize insertion index
            while i < len(self.active_segments) and (
                self.active_segments[i].is_horizontal or
                self.active_segments[i].get_x_at_y(y - 1e-6) < x
            ):  # Find correct position based on x-coordinate
                i += 1  # Move to next position
            self.active_segments.insert(i, segment)  # Insert segment at index i

    def delete(self, segment):  # Method to remove a segment from status
        # Remove a segment if present
        if segment in self.active_segments:  # Check if segment exists in list
            self.active_segments.remove(segment)  # Remove segment

    def segments_containing_point(self, p):  # Method to find segments containing a point
        # Return segments that contain the point p
        result = []  # Initialize list for segments containing point
        for seg in self.active_segments:  # Iterate through active segments
            if seg.upper != p and seg.lower != p:  # Exclude segments where point is an endpoint
                y_min = min(seg.upper[1], seg.lower[1])  # Get minimum y of segment
                y_max = max(seg.upper[1], seg.lower[1])  # Get maximum y of segment
                if y_min - 1e-6 <= p[1] <= y_max + 1e-6:  # Check if point's y is within segment's y-range
                    x = seg.get_x_at_y(p[1])  # Get x-coordinate of segment at point's y
                    if seg.is_horizontal:  # If segment is horizontal
                        x_min = min(seg.upper[0], seg.lower[0])  # Get minimum x of segment
                        x_max = max(seg.upper[0], seg.lower[0])  # Get maximum x of segment
                        if x_min - 1e-6 <= p[0] <= x_max + 1e-6:  # Check if point's x is within segment's x-range
                            result.append(seg)  # Add segment to result
                    elif abs(x - p[0]) < 1e-6:  # If non-horizontal and x matches point's x
                        result.append(seg)  # Add segment to result
        return result  # Return list of segments containing point

# ===========================
# Handle an event point
# ===========================
def handle_event_point(p, T, Q, point_segment_map, output, seen_points):  # Function to process a sweep line event
    U = point_segment_map.get(('U', p), [])  # Get segments starting at point p
    L = point_segment_map.get(('L', p), [])  # Get segments ending at point p
    C = T.segments_containing_point(p)       # Get segments passing through point p
    involved = list(set(U + L + C))  # Combine and deduplicate involved segments
    point_tuple = (round(p[0], 8), round(p[1], 8))  # Round point coordinates for comparison

    # Report intersection if more than one segment is involved
    if len(involved) > 1 and point_tuple not in seen_points:  # Check for multiple segments and unseen point
        intersection_type = classify_intersection(p, involved)  # Determine intersection type
        print(f"Intersection at {p} with segments: {[s.id for s in involved]} → type: {intersection_type}")  # Print intersection details
        output.append((p, involved))  # Add intersection to output
        seen_points.add(point_tuple)  # Mark point as seen

    # Update the status structure
    for s in L + C:  # Remove segments ending at or passing through p
        T.delete(s)  # Delete segment from status
    for s in U + C:  # Insert segments starting at or passing through p
        T.insert(s, p[1])  # Insert segment into status at y-coordinate

    # Check new intersections
    for i in range(len(T.active_segments) - 1):  # Iterate through pairs of consecutive active segments
        s1 = T.active_segments[i]  # First segment
        s2 = T.active_segments[i + 1]  # Second segment
        find_new_event(s1, s2, p, Q, seen_points)  # Check for new intersection event

# ===========================
# Check and enqueue new intersection event
# ===========================
def find_new_event(s1, s2, p, Q, seen_points):  # Function to find and add new intersection events
    if s1 is None or s2 is None or s1 == s2:  # Skip if segments are invalid or identical
        return  # Exit function
    if do_intersect(s1, s2):  # Check if segments intersect
        ipt = compute_intersection_point(s1, s2)  # Compute intersection point
        if ipt and (ipt[1] < p[1] - 1e-6 or (abs(ipt[1] - p[1]) < 1e-6 and ipt[0] > p[0] + 1e-6)):  # Check if intersection is below or right of current point
            Q.add(Event(ipt, 'intersection', [s1, s2]))  # Add intersection event to queue

# ===========================
# Compute intersection point of two segments
# ===========================
def compute_intersection_point(s1, s2):  # Function to calculate intersection point of two segments
    x1, y1 = s1.upper  # Upper point of first segment
    x2, y2 = s1.lower  # Lower point of first segment
    x3, y3 = s2.upper  # Upper point of second segment
    x4, y4 = s2.lower  # Lower point of second segment
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)  # Compute denominator for intersection formula
    if abs(denom) < 1e-6:  # Check if lines are parallel (denominator near zero)
        return None  # Return None if no intersection
    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / denom  # Compute x-coordinate of intersection
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / denom  # Compute y-coordinate of intersection
    def between(a, b, c): return min(a, b) - 1e-6 <= c <= max(a, b) + 1e-6  # Helper function to check if value is between two bounds
    if between(x1, x2, px) and between(y1, y2, py) and between(x3, x4, px) and between(y3, y4, py):  # Check if intersection lies within both segments
        return (px, py)  # Return intersection point
    return None  # Return None if intersection is outside segment bounds

# ===========================
# Main intersection algorithm using sweep line
# ===========================
def FINDINTERSECTIONS(segments):  # Main function to find all intersections using sweep line algorithm
    Q = EventQueue()  # Initialize event queue
    T = StatusStructure()  # Initialize status structure
    output = []  # List to store intersection points and segments
    seen_points = set()  # Set to track seen intersection points
    point_segment_map = {}  # Dictionary to map points to segments (upper or lower endpoints)
    for s in segments:  # Iterate through all segments
        point_segment_map.setdefault(('U', s.upper), []).append(s)  # Map upper point to segment
        Q.add(Event(s.upper, 'start', [s]))  # Add start event for segment
        point_segment_map.setdefault(('L', s.lower), []).append(s)  # Map lower point to segment
        Q.add(Event(s.lower, 'end', [s]))  # Add end event for segment
    while not Q.is_empty():  # Process all events in queue
        event = Q.pop()  # Get next event
        handle_event_point(event.point, T, Q, point_segment_map, output, seen_points)  # Handle the event
    return output  # Return list of intersections

# ===========================
# Classify intersection type: endpoint or interior
# ===========================
def classify_intersection(point, segments):  # Function to classify intersection as endpoint or interior
    for s in segments:  # Iterate through involved segments
        if (abs(point[0] - s.upper[0]) < 1e-6 and abs(point[1] - s.upper[1]) < 1e-6) or \
           (abs(point[0] - s.lower[0]) < 1e-6 and abs(point[1] - s.lower[1]) < 1e-6):  # Check if point matches segment endpoint
            return "endpoint"  # Return endpoint type
    return "interior"  # Return interior type if not an endpoint

# ===========================
# Save intersection results to shapefile
# ===========================
def save_intersections_to_shapefile(intersections, output_path, crs):  # Function to save intersections to a shapefile
    data = {'geometry': [], 'type': [], 'seg_ids': []}  # Initialize dictionary for GeoDataFrame
    for point, segs in intersections:  # Iterate through intersections
        kind = classify_intersection(point, segs)  # Classify intersection type
        seg_ids = [s.id for s in segs]  # Get IDs of involved segments
        data['geometry'].append(Point(point))  # Add intersection point
        data['type'].append(kind)  # Add intersection type
        data['seg_ids'].append(','.join(map(str, seg_ids)))  # Add comma-separated segment IDs
    gdf = gpd.GeoDataFrame(data, crs=crs)  # Create GeoDataFrame with specified CRS
    gdf.to_file(output_path)  # Save to shapefile
    print(f"Intersections saved to {output_path}")  # Print confirmation

# ===========================
# Plot segments and intersection points
# ===========================
def plot_segments_and_intersections(gdf_segments, intersections):  # Function to visualize segments and intersections
    fig, ax = plt.subplots(figsize=(8, 6))  # Create figure and axis with specified size
    gdf_segments.plot(ax=ax, color='#FFCC99', linewidth=0.7, label='Segments')  # Plot segments with light orange color
    points = []  # List for intersection points
    colors = []  # List for point colors
    for point, segs in intersections:  # Iterate through intersections
        kind = classify_intersection(point, segs)  # Classify intersection type
        points.append(Point(point))  # Add point to list
        colors.append('red' if kind == 'interior' else 'blue')  # Red for interior, blue for endpoint
    if points:  # If there are intersection points
        gdf_points = gpd.GeoDataFrame(geometry=points, crs=gdf_segments.crs)  # Create GeoDataFrame for points
        gdf_points.plot(ax=ax, color=colors, markersize=40, label='Intersections')  # Plot points with specified colors
    plt.title("Line Segments and Intersections")  # Set plot title
    plt.legend()  # Show legend
    plt.axis('off')  # Hide axes
    plt.tight_layout()  # Adjust layout to fit
    plt.savefig("Exports/intersections_map.png", dpi=300)  # Save plot as PNG with high resolution
    plt.show()  # Display plot

# ===========================
# Main program execution
# ===========================
shapefile_path = "layers/FINAL.shp"  # Define path to input shapefile
segments, gdf_segments = read_segments_from_shapefile(shapefile_path)  # Read segments from shapefile
intersections = FINDINTERSECTIONS(segments)  # Find all intersections
if not os.path.exists('Exports'):  # Check if Exports directory exists
    os.makedirs('Exports')  # Create Exports directory if it doesn't exist
output_shapefile_path = "Exports/intersections.shp"  # Define path for output shapefile
save_intersections_to_shapefile(intersections, output_shapefile_path, gdf_segments.crs)  # Save intersections to shapefile
for point, segs in intersections:  # Iterate through intersections
    seg_ids = [f"S{s.id}" for s in segs]  # Format segment IDs
    kind = classify_intersection(point, segs)  # Classify intersection type
    print(f"Intersection at {point} between {seg_ids} → type: {kind}")  # Print intersection details
plot_segments_and_intersections(gdf_segments, intersections)  # Plot segments and intersections


