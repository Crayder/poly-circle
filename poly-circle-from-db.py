import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
from matplotlib.gridspec import GridSpec
import pandas as pd
import sys
import os
import math
import sqlite3

matplotlib.use("TkAgg")

# Default Configuration Constants
DEFAULT_CONFIG = {
    "DIFFERENCE_THRESHOLD": 0.5,
    "CIRCULARITY_THRESHOLD": 0.0,
    "UNIFORMITY_THRESHOLD": 0.0,
    "ODD_CENTER": "Both",  # Changed to string for selection
    "MIN_RADIUS": 1.0,
    "MAX_RADIUS": 200.0,
    "MIN_DIAMETER": 1,
    "MAX_DIAMETER": 400,
    "MAX_WIDTH": 8
}

overlay_lines = []
overlay_texts = []
overlay_visible = False

# Database path constant
def get_resource_path(relative_path):  # For dev and packaging
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

DATABASE_PATH = get_resource_path("results.db")

def distance_to_center(center_x, center_y, grid_x, grid_y):
    return np.sqrt((grid_x - center_x)**2 + (grid_y - center_y)**2)

def sort_grid_points(center_x, center_y, grid_points):
    def calculate_angle(point):
        x, y = point
        angle = np.arctan2(y - center_y, x - center_x)
        return angle if angle >= 0 else (2 * np.pi + angle)
    return sorted(grid_points, key=calculate_angle)

def create_overlay(ax, center_x, center_y, grid_points):
    global overlay_lines, overlay_texts
    overlay_lines.clear()
    overlay_texts.clear()

    sorted_pts = sort_grid_points(center_x, center_y, grid_points)
    num_points = len(sorted_pts)

    for i in range(num_points):
        A = sorted_pts[i]
        B = sorted_pts[(i + 1) % num_points]
        Ax, Ay = A
        Bx, By = B

        dx = Bx - Ax
        dy = By - Ay

        if dx == 0 or dy == 0:
            line_artist = ax.plot([Ax, Bx], [Ay, By], color="black", zorder=10)
            overlay_lines.extend(line_artist)
            length = abs(dx) if dy == 0 else abs(dy)
            mx, my = (Ax + Bx)/2, (Ay + By)/2
            text_artist = ax.text(mx, my, f"{int(length)}", color="black", fontsize=8, zorder=30,
                                  ha='center', va='center', bbox=dict(facecolor='white', alpha=0.8))
            overlay_texts.append(text_artist)
        else:
            C1 = (Ax, By)
            C2 = (Bx, Ay)
            distC1 = distance_to_center(center_x, center_y, C1[0], C1[1])
            distC2 = distance_to_center(center_x, center_y, C2[0], C2[1])
            C = C1 if distC1 < distC2 else C2
            Cx, Cy = C

            line_artist = ax.plot([Ax, Bx], [Ay, By], color="black", zorder=10)
            overlay_lines.extend(line_artist)
            AC = ax.plot([Ax, Cx], [Ay, Cy], color="red", zorder=10)
            BC = ax.plot([Bx, Cx], [By, Cy], color="red", zorder=10)
            overlay_lines.extend(AC)
            overlay_lines.extend(BC)

            AC_length = int(round(math.sqrt((Ax - Cx)**2 + (Ay - Cy)**2)))
            BC_length = int(round(math.sqrt((Bx - Cx)**2 + (By - Cy)**2)))

            mACx, mACy = (Ax + Cx)/2, (Ay + Cy)/2
            mBCx, mBCy = (Bx + Cx)/2, (By + Cy)/2

            text_AC = ax.text(mACx, mACy, f"{AC_length}", color="black", fontsize=8, zorder=30,
                              ha='center', va='center', bbox=dict(facecolor='white', alpha=0.8))
            text_BC = ax.text(mBCx, mBCy, f"{BC_length}", color="black", fontsize=8, zorder=30,
                              ha='center', va='center', bbox=dict(facecolor='white', alpha=0.8))
            overlay_texts.append(text_AC)
            overlay_texts.append(text_BC)

def toggle_overlay(canvas):
    global overlay_visible
    if canvas is None:
        return
    overlay_visible = not overlay_visible
    for artist in overlay_lines + overlay_texts:
        artist.set_visible(overlay_visible)
    canvas.draw()

def create_plot(odd_center, tested_radius, sides, real_radius, max_diff, max_width, diameter, circularity, uniformity, grid_points):
    if odd_center == "Odd":
        center_x, center_y = 0.5, 0.5
    elif odd_center == "Even":
        center_x, center_y = 0.0, 0.0
    else:  # Both
        center_x, center_y = 0.0, 0.0

    fig = plt.Figure(figsize=(8, 8))
    gs = GridSpec(1, 1, figure=fig)
    ax = fig.add_subplot(gs[0, 0])

    theta = np.linspace(0, 2 * np.pi, 500)
    circle_x = center_x + tested_radius * np.cos(theta)
    circle_y = center_y + tested_radius * np.sin(theta)
    ax.plot(circle_x, circle_y, color="blue")

    ax.scatter(center_x, center_y, color="red")

    polygon_x = [p[0] for p in grid_points]
    polygon_y = [p[1] for p in grid_points]
    polygon_x.append(grid_points[0][0])
    polygon_y.append(grid_points[0][1])
    ax.plot(polygon_x, polygon_y, color="black")
    ax.scatter([p[0] for p in grid_points], [p[1] for p in grid_points], color="orange")

    approx_radius = max(tested_radius, real_radius)
    grid_min_x = int(np.floor(center_x - approx_radius - 1))
    grid_max_x = int(np.ceil(center_x + approx_radius + 1))
    grid_min_y = int(np.floor(center_y - approx_radius - 1))
    grid_max_y = int(np.ceil(center_y + approx_radius + 1))
    ax.set_xticks(np.arange(grid_min_x, grid_max_x + 1, 1))
    ax.set_yticks(np.arange(grid_min_y, grid_max_y + 1, 1))
    ax.grid(True, which="both", linestyle="--", linewidth=0.5)
    ax.set_aspect('equal', adjustable='box')
    ax.set_xlim(center_x - approx_radius - 1, center_x + approx_radius + 1)
    ax.set_ylim(center_y - approx_radius - 1, center_y + approx_radius + 1)

    config_text = (
        f"Odd Center: {'Yes' if odd_center == 'Odd' else ('No' if odd_center == 'Even' else 'Both')}\n"
        f"Tested Radius: {tested_radius:.4f}\n"
        f"Sides: {sides}\n"
        f"Real Radius: {real_radius:.4f}\n"
        f"Max Difference: {max_diff:.4f}\n"
        f"Diameter: {diameter}\n"
        f"Circularity: {circularity:.4f}\n"
        f"Max Width: {max_width}\n"
        f"Uniformity: {uniformity:.4f}"
    )
    ax.text(0.02, 0.98, config_text, transform=ax.transAxes, fontsize=8,
            verticalalignment='top', color="black",
            bbox=dict(facecolor='white', alpha=0.5, edgecolor='none'))

    ax.set_title(f"Polygon (Sides = {sides}, Real Radius = {real_radius:.4f}, Max Diff = {max_diff:.4f}, Diameter = {diameter}, Circularity = {circularity:.4f}, Max Width = {max_width}, Uniformity = {uniformity:.4f})")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")

    return fig

def on_row_selected(event, tree, canvas_frame, odd_center_val, difference_threshold, min_radius, max_radius):
    selected_item = tree.focus()
    if not selected_item:
        return
    data_tuple = tree.item_data.get(selected_item)
    if not data_tuple:
        return

    # The DB row returns the columns in the order: (tested_radius, sides, real_radius, max_diff, max_width, diameter, circularity, grid_points, odd_center, uniformity)
    tested_radius, sides, real_radius, max_diff, max_width, diameter, circularity, grid_str, db_odd_center, uniformity = data_tuple

    # Reconstruct the polygon from grid_points text
    points_str = grid_str.strip()
    point_pairs = points_str.split(')')
    points = []
    for p in point_pairs:
        p = p.strip().strip(',')
        if p.startswith('('):
            p = p[1:]
        if p:
            try:
                x_str, y_str = p.split(',')
                x, y = float(x_str), float(y_str)
                points.append((x, y))
            except ValueError:
                continue
    polygon = tuple(points)

    for widget in canvas_frame.winfo_children():
        widget.destroy()

    toolbar_frame = ttk.Frame(canvas_frame)
    toolbar_frame.pack(side=tk.TOP, fill=tk.X)

    plot_frame = ttk.Frame(canvas_frame)
    plot_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    fig = create_plot(
        odd_center=db_odd_center,
        tested_radius=tested_radius,
        sides=sides,
        real_radius=real_radius,
        max_diff=max_diff,
        max_width=max_width,
        diameter=diameter,
        circularity=circularity,
        uniformity=uniformity,
        grid_points=polygon
    )
    if fig is None:
        return

    canvas = FigureCanvasTkAgg(fig, master=plot_frame)
    canvas.draw()
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(fill=tk.BOTH, expand=1)

    toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
    toolbar.update()
    toolbar.pack(side=tk.TOP, fill=tk.X)

    # Create overlay based on odd_center
    if db_odd_center == 1:
        center_x, center_y = 0.5, 0.5
    else:
        center_x, center_y = 0.0, 0.0
    create_overlay(fig.axes[0], center_x, center_y, polygon)
    for artist in overlay_lines + overlay_texts:
        artist.set_visible(overlay_visible)
    canvas.draw()

    tree.canvas_ref = canvas

def sort_treeview(tree, col, reverse, sort_order):
    l = [(tree.set(k, col), k) for k in tree.get_children('')]
    if not l:
        return

    try:
        # Attempt to convert to float for numeric sorting
        float(l[0][0].replace(',', ''))
        is_numeric = True
    except ValueError:
        is_numeric = False

    if is_numeric:
        l.sort(key=lambda t: float(t[0].replace(',', '')), reverse=reverse)
    else:
        l.sort(reverse=reverse)

    for index, (val, k) in enumerate(l):
        tree.move(k, '', index)

    sort_order[col] = not reverse
    tree.heading(col, text=tree.heading(col)['text'], command=lambda: sort_treeview(tree, col, sort_order[col], sort_order))

def export_to_csv(valid_data, tree):
    if not valid_data:
        messagebox.showinfo("No Data", "There is no data to export.")
        return
    try:
        # Dump database columns into a dataframe
        data = {
            "tested_radius": [f"{r[0]:.4f}" for r in valid_data],
            "sides": [f"{r[1]}" for r in valid_data],
            "real_radius": [f"{r[2]:.4f}" for r in valid_data],
            "max_diff": [f"{r[3]:.4f}" for r in valid_data],
            "max_width": [f"{r[4]}" for r in valid_data],
            "diameter": [f"{r[5]}" for r in valid_data],         # Diameter as integer
            "circularity": [f"{r[6]:.4f}" for r in valid_data],
            "uniformity": [f"{r[9]:.4f}" for r in valid_data],
            "odd_center": ["Yes" if r[8] else "No" for r in valid_data]
        }
        df = pd.DataFrame(data)
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file_path:
            df.to_csv(file_path, index=False)
            messagebox.showinfo("Export Successful", f"Data exported to {file_path}")
    except Exception as e:
        messagebox.showerror("Export Failed", f"Failed to export data: {e}")

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

def on_load_click(odd_center_var, entries_thresholds, entries_radius, entries_diameter, 
                  tree, canvas_frame):
    """
    Load data based on the user inputs and display in the TreeView.
    """
    try:
        # Normal mode
        difference_threshold = float(entries_thresholds["DIFFERENCE_THRESHOLD"].get())
        if difference_threshold < 0:
            raise ValueError("Difference Threshold cannot be negative.")

        circularity_threshold = float(entries_thresholds["CIRCULARITY_THRESHOLD"].get())
        if not (0.0 <= circularity_threshold <= 1.0):
            raise ValueError("Circularity Threshold must be between 0.0 and 1.0.")

        uniformity_threshold = float(entries_thresholds["UNIFORMITY_THRESHOLD"].get())
        if not (0.0 <= uniformity_threshold <= 1.0):
            raise ValueError("Uniformity Threshold must be between 0.0 and 1.0.")

        max_width_threshold = int(entries_thresholds["MAX_WIDTH"].get())
        if not (1 <= max_width_threshold <= 8):
            raise ValueError("Max Width must be between 1 and 8.")

        min_radius = float(entries_radius["MIN_RADIUS"].get())
        max_radius = float(entries_radius["MAX_RADIUS"].get())
        if min_radius < 0 or min_radius > 200:
            raise ValueError("Min Radius must be between 0 and 200.")
        if max_radius < 0 or max_radius > 200:
            raise ValueError("Max Radius must be between 0 and 200.")
        if min_radius > max_radius:
            raise ValueError("Min Radius cannot be greater than Max Radius.")

        min_diameter = int(entries_diameter["MIN_DIAMETER"].get())
        max_diameter = int(entries_diameter["MAX_DIAMETER"].get())
        if not (1 <= min_diameter <= 400):
            raise ValueError("Min Diameter must be between 1 and 400.")
        if not (1 <= max_diameter <= 400):
            raise ValueError("Max Diameter must be between 1 and 400.")
        if min_diameter > max_diameter:
            raise ValueError("Min Diameter cannot be greater than Max Diameter.")

        odd_center_val = odd_center_var.get()  # "Odd", "Even", or "Both"

        rows = load_results_from_db(difference_threshold, circularity_threshold, uniformity_threshold, max_width_threshold,
                                    odd_center_val, min_radius, max_radius, min_diameter, max_diameter)

    except ValueError as ve:
        messagebox.showerror("Invalid Input", str(ve))
        return
    except sqlite3.Error as db_err:
        messagebox.showerror("DB Error", f"Database error: {db_err}")
        return
    except Exception as e:
        messagebox.showerror("Error", str(e))
        return

    # Clear the tree
    for item in tree.get_children():
        tree.delete(item)
    tree.item_data.clear()

    if not rows:
        messagebox.showinfo("No Results", "No polygons found for the query.")
        for widget in canvas_frame.winfo_children():
            widget.destroy()
        return

    # Sort by sides ascending (column index 1 is sides)
    rows = sorted(rows, key=lambda x: x[1])  # x[1] = sides

    # Insert into the TreeView
    # columns = ("tested_radius", "sides", "real_radius", "max_diff", "max_width", "diameter", "circularity", "uniformity", "odd_center")
    for row in rows:
        # row is (tested_radius, sides, real_radius, max_diff, max_width, diameter, circularity, grid_points, odd_center, uniformity)
        tested_radius, sides, real_radius, max_diff, max_width, diameter, circularity, grid_points, oc_val, uniformity = row

        # Insert into the tree
        # We'll show them in the exact order as columns, excluding grid_points
        tree_vals = (
            f"{tested_radius:.4f}",  # tested_radius
            f"{sides}",              # sides
            f"{real_radius:.4f}",    # real_radius
            f"{max_diff:.4f}",       # max_diff
            f"{max_width}",          # max_width
            f"{diameter}",           # diameter
            f"{circularity:.4f}",    # circularity
            f"{uniformity:.4f}",     # uniformity
            "Yes" if oc_val else "No"  # odd_center as string
        )
        # Insert row
        iid = tree.insert("", tk.END, values=tree_vals)
        tree.item_data[iid] = row  # store raw tuple for on_row_selected

    # Auto-select first row
    if tree.get_children():
        first_id = tree.get_children()[0]
        tree.selection_set(first_id)
        tree.focus(first_id)
        # Force on_row_selected to parse/plot the first row
        on_row_selected(None, tree, canvas_frame, odd_center_val, difference_threshold, min_radius, max_radius)

def main():
    global root
    root = tk.Tk()
    root.title("Polygon Radius App (Database Edition)")
    root.geometry("1200x900")

    input_frame = ttk.Frame(root)
    input_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

    # --- Normal Mode Frames ---

    # Thresholds Frame
    thresholds_frame = ttk.LabelFrame(input_frame, text="Thresholds")
    thresholds_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

    # Radius Range Frame
    radius_frame = ttk.LabelFrame(input_frame, text="Radius Range")
    radius_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

    # Diameter Range Frame
    diameter_frame = ttk.LabelFrame(input_frame, text="Diameter Range")
    diameter_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

    # We'll hold these frames in a list so we can hide/show them in custom mode
    normal_mode_frames = [thresholds_frame, radius_frame, diameter_frame]

    # --- Buttons Frame (always visible) ---
    buttons_frame = ttk.Frame(input_frame)
    buttons_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

    # --- Thresholds Frame Inputs ---
    entries_thresholds = {}
    
    # Difference Threshold
    label_diff = ttk.Label(thresholds_frame, text="Difference Threshold:")
    label_diff.grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
    entry_diff = ttk.Entry(thresholds_frame, width=15)
    entry_diff.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
    entry_diff.insert(0, str(DEFAULT_CONFIG["DIFFERENCE_THRESHOLD"]))
    entries_thresholds["DIFFERENCE_THRESHOLD"] = entry_diff

    # Circularity Threshold Entry
    label_circ_thresh = ttk.Label(thresholds_frame, text="Circularity Threshold:")
    label_circ_thresh.grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
    entry_circ_thresh = ttk.Entry(thresholds_frame, width=15)
    entry_circ_thresh.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
    entry_circ_thresh.insert(0, str(DEFAULT_CONFIG["CIRCULARITY_THRESHOLD"]))
    entries_thresholds["CIRCULARITY_THRESHOLD"] = entry_circ_thresh

    # Uniformity Threshold Entry
    label_uniform_thresh = ttk.Label(thresholds_frame, text="Uniformity Threshold:")
    label_uniform_thresh.grid(row=2, column=0, padx=5, pady=5, sticky=tk.E)
    entry_uniform_thresh = ttk.Entry(thresholds_frame, width=15)
    entry_uniform_thresh.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
    entry_uniform_thresh.insert(0, str(DEFAULT_CONFIG["UNIFORMITY_THRESHOLD"]))
    entries_thresholds["UNIFORMITY_THRESHOLD"] = entry_uniform_thresh

    # Max Width
    label_max_width = ttk.Label(thresholds_frame, text="Max Width:")
    label_max_width.grid(row=3, column=0, padx=5, pady=5, sticky=tk.E)
    spin_max_width = ttk.Spinbox(thresholds_frame, from_=1, to=8, width=13)
    spin_max_width.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)
    spin_max_width.set(str(DEFAULT_CONFIG["MAX_WIDTH"]))
    entries_thresholds["MAX_WIDTH"] = spin_max_width

    # Min Radius Entry
    entries_radius = {}
    label_min_radius = ttk.Label(radius_frame, text="Min Radius:")
    label_min_radius.grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
    entry_min_radius = ttk.Entry(radius_frame, width=15)
    entry_min_radius.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
    entry_min_radius.insert(0, str(DEFAULT_CONFIG["MIN_RADIUS"]))
    entries_radius["MIN_RADIUS"] = entry_min_radius

    # Max Radius Entry
    label_max_radius = ttk.Label(radius_frame, text="Max Radius:")
    label_max_radius.grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
    entry_max_radius = ttk.Entry(radius_frame, width=15)
    entry_max_radius.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
    entry_max_radius.insert(0, str(DEFAULT_CONFIG["MAX_RADIUS"]))
    entries_radius["MAX_RADIUS"] = entry_max_radius

    # Min Diameter Entry (Spinbox)
    entries_diameter = {}
    label_min_diameter = ttk.Label(diameter_frame, text="Min Diameter:")
    label_min_diameter.grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
    spin_min_diameter = ttk.Spinbox(diameter_frame, from_=1, to=400, width=13)
    spin_min_diameter.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
    spin_min_diameter.set(str(DEFAULT_CONFIG["MIN_DIAMETER"]))
    entries_diameter["MIN_DIAMETER"] = spin_min_diameter

    # Max Diameter Entry (Spinbox)
    label_max_diameter = ttk.Label(diameter_frame, text="Max Diameter:")
    label_max_diameter.grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
    spin_max_diameter = ttk.Spinbox(diameter_frame, from_=1, to=400, width=13)
    spin_max_diameter.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
    spin_max_diameter.set(str(DEFAULT_CONFIG["MAX_DIAMETER"]))
    entries_diameter["MAX_DIAMETER"] = spin_max_diameter

    # Odd Center Selection
    label_odd_center = ttk.Label(diameter_frame, text="Odd Center:")
    label_odd_center.grid(row=2, column=0, padx=5, pady=5, sticky=tk.E)
    odd_center_var = tk.StringVar(value=DEFAULT_CONFIG["ODD_CENTER"])
    combo_odd_center = ttk.Combobox(diameter_frame, textvariable=odd_center_var, state="readonly",
                                    values=["Both", "Odd", "Even"], width=11)
    combo_odd_center.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)

    # --- Load / Run Query Button ---
    load_button = ttk.Button(buttons_frame, text="Load / Run Query",
                             command=lambda: on_load_click(odd_center_var,
                                                           entries_thresholds,
                                                           entries_radius,
                                                           entries_diameter,
                                                           tree,
                                                           canvas_frame))
    load_button.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

    # Define Treeview Columns (match the DB exactly excluding the grid_points column)
    columns = (
        "tested_radius", "sides", "real_radius", "max_diff",
        "max_width", "diameter", "circularity", "uniformity", "odd_center"
    )

    # Export Button
    export_button = ttk.Button(buttons_frame, text="Export to CSV",
                               command=lambda: export_to_csv(list(tree.item_data.values()), tree))
    export_button.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

    # Overlay Checkbox
    overlay_var = tk.BooleanVar(value=False)
    overlay_check = ttk.Checkbutton(buttons_frame, text="Show Overlay", variable=overlay_var,
                                    command=lambda: toggle_overlay(getattr(tree, 'canvas_ref', None)))
    overlay_check.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

    # Bottom Frame for Treeview and Plot
    bottom_frame = ttk.Frame(root)
    bottom_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Treeview Frame
    table_frame = ttk.Frame(bottom_frame)
    table_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=10, pady=10)

    # Define Treeview with Updated Columns and Horizontal Scrollbar
    tree = ttk.Treeview(table_frame, columns=columns, show='headings', selectmode='browse')
    for col in columns:
        tree.heading(col, text=col.replace("_", " ").title())
        tree.column(col, anchor=tk.CENTER, width=80)
    scrollbar_vertical = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
    scrollbar_horizontal = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=tree.xview)  # Added horizontal scrollbar
    tree.configure(yscroll=scrollbar_vertical.set, xscroll=scrollbar_horizontal.set)
    scrollbar_vertical.pack(side=tk.RIGHT, fill=tk.Y)
    scrollbar_horizontal.pack(side=tk.BOTTOM, fill=tk.X)  # Pack horizontal scrollbar
    tree.pack(fill=tk.BOTH, expand=True)

    tree.item_data = {}

    # Plot Frame
    plot_frame = ttk.Frame(bottom_frame)
    plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
    canvas_frame = ttk.Frame(plot_frame)
    canvas_frame.pack(fill=tk.BOTH, expand=True)

    # Sorting Order Dictionary
    sort_order = {col: False for col in columns}
    for col in columns:
        tree.heading(col, text=col.replace("_", " ").title(), command=lambda _col=col: sort_treeview(tree, _col, sort_order[_col], sort_order))

    # Bind Row Selection
    tree.bind("<<TreeviewSelect>>", lambda event: on_row_selected(
        event,
        tree,
        canvas_frame,
        odd_center_var.get(),
        float(entries_thresholds["DIFFERENCE_THRESHOLD"].get() or 0),
        float(entries_radius["MIN_RADIUS"].get() or 0),
        float(entries_radius["MAX_RADIUS"].get() or 0)
    ))

    root.mainloop()

if __name__ == "__main__":
    main()
