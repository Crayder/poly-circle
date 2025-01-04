# Scrap Mechanic Wedge Circle Generator

This web app lists and displays optimal circular polygons for Scrap Mechanic, allowing you to create
the best possible circles/curves in the game using the new wedge blocks. Every result is pre-calculated
ensuring they are possible in-game. The aim to be able to create circles as near-perfect to being round
as possible given the limitations of the game.

- `Difference Threshold` – The maximum allowed deviation of any vertex from the perfect circle’s boundary. Lower is stricter.
- `Circularity Threshold` – How close the shape is to being perfectly round (1.0 is a perfect circle).
- `Uniformity Threshold` – How similar each side’s length is. Higher means more evenly spaced sides.
- `Max Width` – The largest wedge size allowed. Scrap Mechanic wedges only go up to 8×8.
- `Min/Max Radius` – The smallest/largest radius to show. The radius is how far the outermost vertex is from the center.
- `Min/Max Diameter` – The overall width of the polygon (in blocks).
- `Odd Center` – “Odd” means the circles have odd width, “Even” means the circles have even width, “Both” ignores that filter.

Recommended Use Cases:
- If you want a giant wheel, aim for *higher Circularity* and *higher Uniformity* so it rolls nicely.
- If you need a hollow center or a narrower shape, lower the *Max Width* to avoid large wedges.
