import sqlite3
from constants import DATABASE_PATH

def load_results_from_db(difference_threshold, circularity_threshold, uniformity_threshold, max_width_threshold, odd_center_val,
                         min_radius, max_radius, min_diameter, max_diameter):
    """
    Normal mode fetch: uses parameters to build a query with conditions on max_diff, circularity, uniformity, max_width, etc.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()

    # Start constructing the query
    query = """SELECT tested_radius, sides, real_radius, max_diff, max_width, diameter, 
                      circularity, grid_points, odd_center, uniformity
               FROM results
               WHERE max_diff <= ?
                 AND circularity >= ?
                 AND uniformity >= ?
                 AND max_width <= ?
                 AND tested_radius >= ?
                 AND tested_radius <= ?
                 AND diameter >= ?
                 AND diameter <= ?
            """

    params = [difference_threshold, circularity_threshold, uniformity_threshold, max_width_threshold,
              min_radius, max_radius, min_diameter, max_diameter]

    # Add odd_center condition based on selection
    if odd_center_val == "Odd":
        query += " AND odd_center = ?"
        params.append(1)
    elif odd_center_val == "Even":
        query += " AND odd_center = ?"
        params.append(0)
    # If "Both", do not add any condition on odd_center

    c.execute(query, tuple(params))
    rows = c.fetchall()
    conn.close()
    return rows  # Each row has 10 columns
