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

def deteriorate_large_wedges(wedges):
    """
    Deteriorates large wedges into smaller wedges that are less than 8x8.
    """
    new_wedges = []
    new_rects = []
    for wedge in wedges[:]:
        width = int(abs(wedge['point_b'].x - wedge['point_a'].x))
        height = int(abs(wedge['point_b'].y - wedge['point_a'].y))
        print(f"Checking wedge ({width}x{height}): {wedge}")
        if width > 8 or height > 8:
            num_wedges = math.gcd(width, height)
            new_width = width // num_wedges
            new_height = height // num_wedges
            print(f"Wedge needs to be broken down into {num_wedges} wedges, each {new_width}x{new_height}.")
            for i in range(num_wedges):
                print(f"Iteration {i}")
                new_wedge = {
                    "point_a": Point(0, 0),
                    "point_b": Point(0, 0),
                    "point_c": Point(0, 0),
                    "rotation": wedge['rotation'],
                    "quadrant": wedge['quadrant']
                }
                new_rect = {
                    "x": 0,
                    "y": 0,
                    "width": 0,
                    "height": 0
                }
                # Calculate the points of the new wedge based on the quadrant, and the new rect position.
                if wedge['quadrant'] == 'tl': # Top Left
                    # TODO: THIS WEDGE IS WRONG
                    new_point_a = Point(wedge['point_a'].x + (i * new_width), wedge['point_a'].y + (i * new_height))
                    new_point_b = Point(new_point_a.x + new_width, new_point_a.y + new_height)
                    new_point_c = Point(new_point_b.x, new_point_a.y)
                    new_wedge['point_a'] = new_point_a
                    new_wedge['point_b'] = new_point_b
                    new_wedge['point_c'] = new_point_c
                    # THIS RECT IS CORRECT NOW
                    new_rect['width'] = width - ((i + 1) * new_width)
                    new_rect['height'] = new_height
                    new_rect['x'] = wedge['point_c'].x - new_rect['width']
                    new_rect['y'] = wedge['point_c'].y + (i * new_height)
                if wedge['quadrant'] == 'tr': # Top Right
                    # TODO: THIS WEDGE IS WRONG
                    new_point_a = Point(wedge['point_a'].x + (i * new_width), wedge['point_a'].y - (i * new_height))
                    new_point_b = Point(new_point_a.x + new_width, new_point_a.y - new_height)
                    new_point_c = Point(new_point_a.x, new_point_b.y)
                    new_wedge['point_a'] = new_point_a
                    new_wedge['point_b'] = new_point_b
                    new_wedge['point_c'] = new_point_c
                    # THIS RECT IS CORRECT NOW
                    new_rect['width'] = new_width
                    new_rect['height'] = height - ((i + 1) * new_height)
                    new_rect['x'] = wedge['point_c'].x + (i * new_width)
                    new_rect['y'] = wedge['point_c'].y
                if wedge['quadrant'] == 'br': # Bottom Right
                    # TODO: THIS WEDGE IS WRONG
                    new_point_a = Point(wedge['point_a'].x - (i * new_width), wedge['point_a'].y - (i * new_height))
                    new_point_b = Point(new_point_a.x - new_width, new_point_a.y - new_height)
                    new_point_c = Point(new_point_b.x, new_point_a.y)
                    new_wedge['point_a'] = new_point_a
                    new_wedge['point_b'] = new_point_b
                    new_wedge['point_c'] = new_point_c
                    # THIS RECT IS CORRECT NOW
                    new_rect['width'] = width - ((i + 1) * new_width)
                    new_rect['height'] = new_height
                    new_rect['x'] = wedge['point_c'].x
                    new_rect['y'] = wedge['point_c'].y - ((i + 1) * new_height)
                if wedge['quadrant'] == 'bl': # Bottom Left
                    # TODO: THIS WEDGE IS WRONG
                    new_point_a = Point(wedge['point_a'].x - (i * new_width), wedge['point_a'].y + (i * new_height))
                    new_point_b = Point(new_point_a.x - new_width, new_point_a.y + new_height)
                    new_point_c = Point(new_point_a.x, new_point_b.y)
                    new_wedge['point_a'] = new_point_a
                    new_wedge['point_b'] = new_point_b
                    new_wedge['point_c'] = new_point_c
                    # THIS RECT IS CORRECT NOW
                    new_rect['width'] = new_width
                    new_rect['height'] = height - ((i + 1) * new_height)
                    new_rect['x'] = wedge['point_c'].x - ((i + 1) * new_width)
                    new_rect['y'] = wedge['point_c'].y - new_rect['height']
                # Add the new wedge and rect to the lists.
                new_wedges.append(new_wedge)
                print(f"Adding new_wedge: {new_wedge}")
                # If new rect width is greater than 0, add the new rect to the new_rects list.
                if new_rect['width'] > 0 and new_rect['height'] > 0:
                    new_rects.append(new_rect)
                    print(f"Adding new_rect: {new_rect}")
        else:
            # The wedge is already small enough, add it to the new_wedges list.
            new_wedges.append(wedge)
    return new_wedges, new_rects

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

    return rects, wedges
