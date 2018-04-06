## Upload Datasets
Upload these datasets to CARTO
```
# CARTO dataset name <- File path
hrs_daily_kgh2 <- LongHaul_module/output/HRS_Daily_kgH2.csv
nodes_info <- LongHaul_module/scratch/Nodes_info.csv
arcs_with_lengths <- LongHaul_module/scratch/Arcs_with_lengths.csv
```

## Make `Truck Network Arcs` Layer
Use the following SQL query to make the layer.
Some PostGIS commands are used.
```sql
SELECT
    ST_MakeLine(from_nd.the_geom, to_nd.the_geom) AS the_geom,
    ST_MakeLine(from_nd.the_geom_webmercator, to_nd.the_geom_webmercator) AS the_geom_webmercator,
    from_nd.cartodb_id,
    from_nd.arc_id,
    from_nd.from_node_id,
    to_nd.to_node_id,
    from_nd.len_km
FROM

(SELECT
    arc.cartodb_id,
    nd.the_geom,
    nd.the_geom_webmercator,
    arc.arc_id,
    arc.from_node_id,
    arc.drive_dist_km AS len_km
FROM
    arcs_with_lengths AS arc
    LEFT JOIN
    nodes_info AS nd
    ON (arc.from_node_id=nd.node_id)
) AS from_nd,

(SELECT
    nd.the_geom,
    nd.the_geom_webmercator,
    arc.arc_id,
    arc.to_node_id
FROM
    arcs_with_lengths AS arc
    LEFT JOIN
    nodes_info AS nd
    ON (arc.to_node_id=nd.node_id)
) AS to_nd

WHERE from_nd.arc_id=to_nd.arc_id
```

## Make `Candidate Sites` Layer
This layer is simply the `nodes_info` dataset
```sql
SELECT * FROM nodes_info
```

## Make `HRS Daily kgH2` Layer
Join `hrs_daily_kgh2` layer with `nodes_info` layer
```sql
SELECT
    hrs.cartodb_id AS cartodb_id,
    node.the_geom AS the_geom,
    node.the_geom_webmercator AS the_geom_webmercator,
    node.node_name AS node_name,
    hrs.daily_kgh2 AS daily_kgh2
FROM
    hrs_daily_kgh2 AS hrs
    LEFT JOIN
    nodes_info AS node
    ON hrs.hrs_node_id=node.node_id
```


