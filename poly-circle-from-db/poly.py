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

def determine_quadrant(point, center_x, center_y):
    """
    Determines the quadrant of a point relative to the center.
    Returns one of 'tl', 'tr', 'br', 'bl' for top-left, top-right, bottom-right, bottom-left.
    """
    x, y = point
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

        #### print(f"[START] Processing edge from A {A} to B {B}")

        delta_x = B.x - A.x
        delta_y = B.y - A.y

        #### print(f"Delta X: {delta_x}, Delta Y: {delta_y}")

        if delta_x == 0 or delta_y == 0:
            #### print("Edge is vertical or horizontal, not a wedge.")
            # Vertical or Horizontal Line (already handled in plotting)
            # A.x < center and A.x equals B.x
            if A.x < center_x and B.x == A.x:
                #### print(f"Is a left edge, adding A {A} to B {B} to left_edges.")
                # Left vertical edge
                left_edges.append({"point_a": A, "point_b": B})
        else:
            #### print("Edge is diagonal, creating wedge.")
            # Diagonal Line, need to create a wedge
            quadrant = determine_quadrant(A, center_x, center_y)
            wedge = {
                "point_a": A,
                "point_b": B,
                "point_c": None,
                "rotation": {"xaxis": 3, "zaxis": 0},
                "quadrant": quadrant
            }

            if quadrant == "tl":
                #### print("Is a top-left wedge:")
                # Top-Left Quadrant
                C = Point(A.x + delta_x, A.y)
                wedge["point_c"] = C
                wedge["rotation"]["zaxis"] = -1
                #### print(f" - Wedge: {wedge}")
                #### print(f" - Left edge: C {C} to B {B}")
                left_edges.append({"point_a": C, "point_b": B})
            elif quadrant == "tr":
                #### print("Is a top-right wedge:")
                # Top-Right Quadrant
                C = Point(A.x, A.y + delta_y)
                wedge["point_c"] = C
                wedge["rotation"]["zaxis"] = 2
                #### print(f" - Wedge: {wedge}")
                # No left edge to add
            elif quadrant == "br":
                #### print("Is a bottom-right wedge:")
                # Bottom-Right Quadrant
                C = Point(A.x + delta_x, A.y)
                wedge["point_c"] = C
                wedge["rotation"]["zaxis"] = 1
                #### print(f" - Wedge: {wedge}")
                # No left edge to add
            elif quadrant == "bl":
                #### print("Is a bottom-left wedge:")
                # Bottom-Left Quadrant
                C = Point(A.x, A.y + delta_y)
                wedge["point_c"] = C
                wedge["rotation"]["zaxis"] = -2
                #### print(f" - Wedge: {wedge}")
                #### print(f" - Left edge: A {A} to C {C}")
                left_edges.append({"point_a": A, "point_b": C})

            wedges.append(wedge)

    # Process left_edges to create rects
    for edge in left_edges:
        point_a = edge["point_a"]
        point_b = edge["point_b"]
        #### print(f"Processing left edge from A {point_a} to B {point_b}")

        rect = {
            "x": point_a.x,
            "y": point_a.y,
            "width": abs(point_a.x - center_x) * 2,
            "height": abs(point_a.y - point_b.y)
        }
        #### print(f" - Rect: {rect}")
        rects.append(rect)

    return rects, wedges
