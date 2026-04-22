
// Example Leaflet rendering logic

routes.forEach((route, index) => {
  const color = index === bestRouteId ? "green" : "blue";

  L.geoJSON(route.geometry, {
    style: {
      color: color,
      weight: index === bestRouteId ? 6 : 3
    }
  }).addTo(map);
});
