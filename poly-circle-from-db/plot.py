import matplotlib
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from constants import DEFAULT_CONFIG
import numpy as np
import math

matplotlib.use("TkAgg")

overlay_lines = []
overlay_texts = []

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

def set_overlay_visibility(ax, canvas, visible):
    for artist in overlay_lines + overlay_texts:
        artist.set_visible(visible)
    canvas.draw()

def create_plot(odd_center, tested_radius, sides, real_radius, max_diff, max_width, diameter, circularity, uniformity, grid_points):
    if odd_center == "Odd":
        center_x, center_y = 0.5, 0.5
    elif odd_center == "Even":
        center_x, center_y = 0.0, 0.0
    else:  # Both (for safety, though rows won't have "Both")
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

    ax.set_title(f"Polygon (Sides = {sides}, Real Radius = {real_radius:.4f}, Max Diff = {max_diff:.4f}, "
                 f"Diameter = {diameter}, Circularity = {circularity:.4f}, Max Width = {max_width}, "
                 f"Uniformity = {uniformity:.4f})")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")

    return fig, ax
