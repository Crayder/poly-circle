import math
from collections import namedtuple

# Define a simple Point namedtuple for clarity
Point = namedtuple('Point', ['x', 'y'])

def distance_to_center(center_x, center_y, grid_x, grid_y):
    return math.sqrt((grid_x - center_x)**2 + (grid_y - center_y)**2)

def sort_grid_points(center_x, center_y, grid_points):
    def calculate_angle(point):
        x, y = point
        angle = math.atan2(y - center_y, x - center_x)
        return angle if angle >= 0 else (2 * math.pi + angle)
    # Sort in descending order for clockwise
    return sorted(grid_points, key=calculate_angle, reverse=True)

def determine_quadrant(point_a, point_b, center_x, center_y):
    """
    Determines the quadrant of a point relative to the center.
    Returns one of 'tl', 'tr', 'br', 'bl' for top-left, top-right, bottom-right, bottom-left.
    """
    # First get middle point between A and B
    x = (point_a.x + point_b.x) / 2
    y = (point_a.y + point_b.y) / 2

    # Now determine the quadrant of their middle point
    if x < center_x and y >= center_y:
        return 'tl'
    elif x >= center_x and y >= center_y:
        return 'tr'
    elif x >= center_x and y < center_y:
        return 'br'
    elif x < center_x and y < center_y:
        return 'bl'

def convert_polygon_to_blueprint(grid_points, center_x, center_y):
    """
    Converts a polygon defined by grid_points into rects and wedges for blueprint export.
    Returns two lists: rects and wedges.
    """
    rects = []
    wedges = []
    left_edges = []

    sorted_pts = sort_grid_points(center_x, center_y, grid_points)
    num_points = len(sorted_pts)

    for i in range(num_points):
        A = Point(*sorted_pts[i])
        B = Point(*sorted_pts[(i + 1) % num_points])

        delta_x = B.x - A.x
        delta_y = B.y - A.y

        if delta_x == 0 or delta_y == 0:
            # Vertical or Horizontal Line (already handled in plotting)
            if A.x < center_x and (B.x == A.x or B.x == 0):
                # Left vertical edge
                left_edges.append({"point_a": A, "point_b": B})
        else:
            # Diagonal Line, need to create a wedge
            quadrant = determine_quadrant(A, B, center_x, center_y)
            wedge = {
                "point_a": A,
                "point_b": B,
                "point_c": None,
                "rotation": {"xaxis": 3, "zaxis": 0},
                "quadrant": quadrant
            }

            if quadrant == "tl":
                # Top-Left Quadrant
                C = Point(A.x + delta_x, A.y)
                wedge["point_c"] = C
                wedge["rotation"]["zaxis"] = -1
                left_edges.append({"point_a": C, "point_b": B})
            elif quadrant == "tr":
                # Top-Right Quadrant
                C = Point(A.x, A.y + delta_y)
                wedge["point_c"] = C
                wedge["rotation"]["zaxis"] = 2
                # No left edge to add
            elif quadrant == "br":
                # Bottom-Right Quadrant
                C = Point(A.x + delta_x, A.y)
                wedge["point_c"] = C
                wedge["rotation"]["zaxis"] = 1
                # No left edge to add
            elif quadrant == "bl":
                # Bottom-Left Quadrant
                C = Point(A.x, A.y + delta_y)
                wedge["point_c"] = C
                wedge["rotation"]["zaxis"] = -2
                left_edges.append({"point_a": A, "point_b": C})

            wedges.append(wedge)

    # Process left_edges to create rects
    for edge in left_edges:
        point_a = edge["point_a"]
        point_b = edge["point_b"]

        # If 0 width skip this edge
        if point_a.x == center_x:
            continue

        rect = {
            "x": point_a.x,
            "y": point_a.y,
            "width": abs(point_a.x - center_x) * 2,
            "height": abs(point_a.y - point_b.y)
        }
        rects.append(rect)
    
    # TODO: Need to break down wedges here. Specifically ones that are bigger than 8x8. Then generate rects for the empty space created within the wedge.
    # Loop through the wedges. Check size.
    # If size is greater than 8x8. We already know the wedge can be broken down, since the database already only allows 8x8.
    #   Calculate smaller wedge size by getting greatest common divisor of width and height. Divide width and height by that number. Keep track of how many smaller wedges we need.
    #   Create new wedges that are the size of the smaller wedge.
    #   Position the smaller wedges within the larger wedge so the diagonal line is the same. Rotation for each will be the same as the larger wedge.
    #   Add the smaller wedges to the wedges list. Remove the larger wedge.

    return rects, wedges
