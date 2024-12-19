import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from matplotlib.gridspec import GridSpec
from tkinter import filedialog
import pandas as pd
import os
import math
import sqlite3

matplotlib.use("TkAgg")

# Default Configuration Constants
DEFAULT_CONFIG = {
    "DIFFERENCE_THRESHOLD": 0.5,
    "ODD_CENTER": False,
    "MIN_RADIUS": 1.0,
    "MAX_RADIUS": 200.0,
    "MIN_DIAMETER": 1,
    "MAX_DIAMETER": 400,
    "CIRCULARITY_THRESHOLD": 0.0
}

overlay_lines = []
overlay_texts = []
overlay_visible = False

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

def create_plot(odd_center, tested_radius, sides, real_radius, max_diff, diameter, circularity, grid_points):
    if odd_center == 1:
        center_x, center_y = 0.5, 0.5
    else:
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
        f"Odd Center: {'Yes' if odd_center == 1 else 'No'}\n"
        f"Tested Radius: {tested_radius:.4f}\n"
        f"Sides: {sides}\n"
        f"Real Radius: {real_radius:.4f}\n"
        f"Max Difference: {max_diff:.4f}\n"
        f"Diameter: {diameter}\n"
        f"Circularity: {circularity:.4f}"
    )
    ax.text(0.02, 0.98, config_text, transform=ax.transAxes, fontsize=8,
            verticalalignment='top', color="black",
            bbox=dict(facecolor='white', alpha=0.5, edgecolor='none'))

    ax.set_title(f"Polygon (Sides = {sides}, Real Radius = {real_radius:.4f}, Max Diff = {max_diff:.4f}, Diameter = {diameter}, Circularity = {circularity:.4f})")
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

    tested_radius, sides, real_radius, max_diff, diameter, circularity, polygon, db_odd_center = data_tuple

    # Determine center based on ODD_CENTER
    if db_odd_center:
        center_x, center_y = 0.5, 0.5
    else:
        center_x, center_y = 0.0, 0.0

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
        diameter=diameter,
        circularity=circularity,
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
    tree.heading(col, command=lambda: sort_treeview(tree, col, sort_order[col], sort_order))

def export_to_csv(valid_data, tree):
    if not valid_data:
        messagebox.showinfo("No Data", "There is no data to export.")
        return
    try:
        min_circularity = getattr(tree, 'min_circularity', None)
        if min_circularity is None:
            min_circularity = 0.0

        data = {
            "Tested Radius": [f"{r[0]:.4f}" for r in valid_data],
            "Sides": [f"{r[1]}" for r in valid_data],
            "Real Radius": [f"{r[2]:.4f}" for r in valid_data],
            "Max Difference": [f"{r[3]:.4f}" for r in valid_data],
            "Diameter": [f"{r[4]}" for r in valid_data],
            "Circularity": [
                f"{((r[5] - min_circularity)/(1 - min_circularity) if (1 - min_circularity) != 0 else 1.0):.4f}" 
                for r in valid_data
            ],   # Scaled Circularity based on database lower bound
            "Odd Center": ["Yes" if r[7] else "No" for r in valid_data]
        }
        df = pd.DataFrame(data)
        file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                                 filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if file_path:
            df.to_csv(file_path, index=False)
            messagebox.showinfo("Export Successful", f"Data exported to {file_path}")
    except Exception as e:
        messagebox.showerror("Export Failed", f"Failed to export data: {e}")

def load_results_from_db(difference_threshold, circularity_threshold, odd_center_val, min_radius, max_radius, min_diameter, max_diameter):
    conn = sqlite3.connect("results.db")
    c = conn.cursor()

    # Retrieve the minimum circularity from the entire database
    c.execute("SELECT MIN(circularity) FROM results")
    min_circularity_row = c.fetchone()
    min_circularity = min_circularity_row[0] if min_circularity_row[0] is not None else 0.0

    c.execute("""SELECT tested_radius, sides, real_radius, max_diff, diameter, circularity, grid_points, odd_center 
                 FROM results 
                 WHERE max_diff <= ? AND circularity >= ? AND odd_center = ? AND tested_radius >= ? AND tested_radius <= ?
                 AND diameter >= ? AND diameter <= ?""",
              (difference_threshold, circularity_threshold, odd_center_val, min_radius, max_radius, min_diameter, max_diameter))
    rows = c.fetchall()
    conn.close()

    final_results = []
    for row in rows:
        tested_radius, sides, real_radius, max_diff, diameter, circularity, grid_str, db_odd_center = row
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
                    points.append((x,y))
                except ValueError:
                    continue  # Skip malformed points (though this should not happen if the database is correct)
        polygon = tuple(points)
        final_results.append((tested_radius, sides, real_radius, max_diff, diameter, circularity, polygon, db_odd_center))

    return final_results, min_circularity

def on_load_click(odd_center_var, entries_thresholds, entries_radius, entries_diameter, tree, canvas_frame):
    try:
        difference_threshold = float(entries_thresholds["DIFFERENCE_THRESHOLD"].get())
        if difference_threshold < 0:
            raise ValueError("Difference Threshold cannot be negative.")

        circularity_threshold = float(entries_thresholds["CIRCULARITY_THRESHOLD"].get())
        if not (0.0 <= circularity_threshold <= 1.0):
            raise ValueError("Circularity Threshold must be between 0.0 and 1.0.")

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
    except ValueError as ve:
        messagebox.showerror("Invalid Input", str(ve))
        return

    odd_center_val = 1 if odd_center_var.get() else 0
    circularity_threshold = float(entries_thresholds["CIRCULARITY_THRESHOLD"].get())
    results, min_circularity = load_results_from_db(difference_threshold, circularity_threshold, odd_center_val, min_radius, max_radius, min_diameter, max_diameter)

    for item in tree.get_children():
        tree.delete(item)
    tree.item_data.clear()

    if not results:
        messagebox.showinfo("No Results", "No polygons found in the database meeting the given criteria.")
        for widget in canvas_frame.winfo_children():
            widget.destroy()
        return

    # Sort by sides ascending
    results.sort(key=lambda x: x[1])
    tree.min_circularity = min_circularity

    for data_tuple in results:
        tested_radius, sides, real_radius, max_diff, diameter, circularity, polygon, db_odd_center = data_tuple
        if (1 - min_circularity) != 0:
            scaled_circularity = (circularity - min_circularity) / (1 - min_circularity)
        else:
            scaled_circularity = 1.0
        scaled_circularity = max(0.0, scaled_circularity)  # Ensure non-negative

        iid = tree.insert("", tk.END, values=(
            f"{tested_radius:.4f}",
            f"{sides}",
            f"{real_radius:.4f}",
            f"{max_diff:.4f}",
            "Yes" if db_odd_center else "No",
            f"{diameter}",
            f"{scaled_circularity:.4f}"
        ))
        tree.item_data[iid] = data_tuple

    # Automatically select first
    if tree.get_children():
        tree.selection_set(tree.get_children()[0])
        tree.focus(tree.get_children()[0])
        on_row_selected(None, tree, canvas_frame, odd_center_val, difference_threshold, min_radius, max_radius)

def main():
    global root
    root = tk.Tk()
    root.title("Polygon Radius App (Database Edition)")
    root.geometry("1200x900")

    input_frame = ttk.Frame(root)
    input_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

    # Options Frame
    options_frame = ttk.LabelFrame(input_frame, text="Options")
    options_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

    # Thresholds Frame
    thresholds_frame = ttk.LabelFrame(input_frame, text="Thresholds")
    thresholds_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

    # Radius Range Frame
    radius_frame = ttk.LabelFrame(input_frame, text="Radius Range")
    radius_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

    # Diameter Range Frame
    diameter_frame = ttk.LabelFrame(input_frame, text="Diameter Range")
    diameter_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

    # Buttons Frame
    buttons_frame = ttk.Frame(input_frame)
    buttons_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

    # Odd Center Checkbox
    odd_center_var = tk.BooleanVar(value=DEFAULT_CONFIG["ODD_CENTER"])
    odd_center_chk = ttk.Checkbutton(options_frame, text="Odd Center", variable=odd_center_var)
    odd_center_chk.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

    # Difference Threshold Entry
    entries_thresholds = {}
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

    # Load Button
    load_button = ttk.Button(buttons_frame, text="Load",
                             command=lambda: on_load_click(odd_center_var, entries_thresholds, entries_radius, entries_diameter, tree, canvas_frame))
    load_button.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

    # Define Treeview Columns
    columns = ("Tested Radius", "Sides", "Real Radius", "Max Difference", "Odd Center", "Diameter", "Circularity")

    # Export Button
    export_button = ttk.Button(buttons_frame, text="Export to CSV", command=lambda: export_to_csv(list(tree.item_data.values()), tree))
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

    # Define Treeview with Updated Columns
    tree = ttk.Treeview(table_frame, columns=columns, show='headings', selectmode='browse')
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor=tk.CENTER, width=90)
    scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
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
        tree.heading(col, text=col, command=lambda _col=col: sort_treeview(tree, _col, sort_order[_col], sort_order))

    # Bind Row Selection
    tree.bind("<<TreeviewSelect>>", lambda event: on_row_selected(
        event,
        tree,
        canvas_frame,
        1 if odd_center_var.get() else 0,
        float(entries_thresholds["DIFFERENCE_THRESHOLD"].get()),
        float(entries_radius["MIN_RADIUS"].get()),
        float(entries_radius["MAX_RADIUS"].get())
    ))

    root.mainloop()

if __name__ == "__main__":
    main()
