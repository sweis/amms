# Aggregated Mobility Metrics Schema

## Overview
The Aggregate Mobility Metrics Schema (AMMS) specifies a portable, compact schema for sharing aggregated mobility data with cities. At a high-level, AMMS allows one to define arbitrary geographic zones and aggregate data on an hourly basis by zone. AMMS also supports a privacy level, which may be used as a k-anonymity or l-diversity level to apply to different aggregated metrics.

The schema includes:
* Total trips, distance, & duration by hour
* Pickups & drop-offs by zone & hour
* Trip volumes by zone & hour, with arbitrary k-anonymity
* Flow between pickup and dropoff zones & hour, with arbitrary l-diversity

AMMS is specified as a Protocol Buffer, which provides a portable binary format supporting major languages and easy conversion to JSON. AMMS is input agnostic and compatible with Mobility Data Specification (MDS) JSON input. An AMMS protocol buffer output is typical than 1% of the size of the raw MDS input data.

## Building Python Sample Code

`make` will run `protoc --python_out=pb/ amms.proto` and run the unit tests under the `tests/` directory.

### Dependencies
* python3
* protobuf, e.g. `brew install protobuf`

## Demo Python Code Usage

### readtrips.py

`readtrips` will read a file in either JSON, CSV, or PBF (protobuf) format and output as PBF. It will optionally suppress data using the given `privacy` parameter. Currently, `readtrips` will map GPS coordinates to zones by rounding coordinates to 3 decimal digits.

#### Usage
```
$ python3 readtrips.py -h
usage: readtrips.py [-h] [--period PERIOD] [--cycle_length CYCLE_LENGTH]
                    [--output_filename OUTPUT_FILENAME] [--suppress]
                    [--suppress_prefix SUPPRESS_PREFIX] [--accuracy ACCURACY]
                    [--privacy PRIVACY]
                    input_filename

Aggregate MDS trip data into a Metrics protocol buffer

positional arguments:
  input_filename        Input filname. Must end with .json, .csv., or .pbf

optional arguments:
  -h, --help            show this help message and exit
  --period PERIOD       Time period in seconds. Hour by default.
  --cycle_length CYCLE_LENGTH
                        The number of periods in a cycle. If provided, periods
                        will be aggregated on a cycle, e.g. the same hour of a
                        day will be tallied.
  --output_filename OUTPUT_FILENAME
                        Output filename
  --suppress            Output suppressed flows subject to k-anonymity
  --suppress_prefix SUPPRESS_PREFIX
                        Output filename prefix for suppressed flows.
                        [prefix]-[k].pbf
  --accuracy ACCURACY   Decimal digits of GPS accuracy used for zones
  --privacy PRIVACY     k-anonymity or l-diversity for suppressed output
```

#### Example Run
```
$ python3 readtrips.py sampledata/tiny-trips.json
DEBUG:root:Reading sampledata/tiny-trips.json
DEBUG:root:Read 7 trips
DEBUG:root:Writing to output.pbf
DEBUG:root:Suppressing flows with l-diversity of 5
DEBUG:root:Writing to suppress-5.pbf
```

### pbftojson.py

`pbftojson` is self explanatory. It reads an AMMS PBF file and outputs it as JSON, either printing it to stdout or saving as a file.

#### Usage
```$ python3 pbftojson.py -h
usage: pbftojson.py [-h] [--output_filename OUTPUT_FILENAME] input_filename

Aggregate MDS trip data into a Metrics protocol buffer

positional arguments:
  input_filename        Input PBF filname

optional arguments:
  -h, --help            show this help message and exit
  --output_filename OUTPUT_FILENAME
                        Output JSON filename. If not provided, output will be
                        printed.
```

#### Example Run
```
$ python3 pbftojson.py sampledata/tiny-trips.pbf
{
  "geoIds": {
    "0": "-86.723:36.116",
    "1": "-86.722:36.116",
...
}
```

### demostats.py
`demostats` is a basic demonstration of using the AMMS PBF file to generate statistics and visualize them.

```
$ Period: 3600 seconds Cycle length: 24
Daily trips: 417
Trips by period    Min:      8     Ave:     17     Max:     26
▄█▄▄▄▂▄▃▄▄▃▅▇▁▅▇▄▄▃▆▆▅▇▆
Average distance   Min:    825 M   Ave:   1283 M   Max:   1789 M
▄▅█▂▃▄▄▅▅█▅▂▅▆▅▆▃▂▄▄▅▄▆▁
Average duration   Min:    599 s   Ave:    943 s   Max:   1324 s
▄▄█▂▃▃▄▅▅█▅▂▅▆▄▆▃▃▃▄▄▅▆▁
Average speed      Min:   1.29 M/s Ave:   1.36 M/s Max:   1.47 M/s
▄▅▃▄▅█▂▂▃▅▂▄▅▂▅▄▃▁▅▇▆▁▂▄

Top Trip Volumes
Period    Lat       Long      Count
3         -86.796   36.137    14
5         -86.773   36.170    14
6         -86.773   36.170    14
7         -86.773   36.170    12
3         -86.792   36.152    11
4         -86.796   36.137    11
4         -86.773   36.170    11
4         -86.775   36.157    10
7         -86.797   36.135    10
13        -86.769   36.143    10

Privacy level: 0
Flows Suppressed: 0.00%
```

## Background
Cities need for mobility metrics for planning, regulatory, and safety purposes and typically request raw, trip-level data. This is problematic for privacy since observing the endpoints of a trip may tie a location associated with an individual (e.g. your house) to a sensitive location. AMMS addresses this concern by aggregating data that can answer regulatory questions while protecting individual location privacy through minimum privacy thresholds.

SharedStreets’ Mobility Metrics is an existing mobility data aggregation tool which generates JSON data files and HTML reports with data visualization. The JSON data files are in an ad hoc format without a clear specification. AMMS is a more efficient representation of much of the same data, and can be easily converted back to JSON with built-in protocol buffer support if needed.

In fairness, Mobility Metrics offers more units of aggregation including street, hex bin, and arbitrary geographic zone in periods of minutes, hours, and days. AMMS only supports aggregation by arbitrary zone and hour.

AMMS also omits fares and vehicle count data, so cannot be used for utilization or revenue metrics. However, it can easily be extended to support additional metrics if needed.

## Privacy Suppression

**Traffic flows** are the most privacy sensitive field since observing one end of a trip may link an individual with the other end. For instance, seeing a unique flow in the data and linking an identity to an endpoint would reveal the source or destination of the trip.

Trip **k-anonymity**, meaning there must be k trips between two endpoints, is not sufficient in this case. If every trip from a pickup spot goes to the same destination, you learn where any observed passenger from that source is going.

There needs to be a diversity of potential sources or destinations, that is, **L-diversity**. Thus, for every flow that is reported in a time window, a pickup must have at least L different potential drop-offs and every dropoff must have L potential pickups.

For **trip volumes**, there is no direct linkage between endpoints unless there is a unique path that does not intersect any other paths. We can apply a k-anonymity metric to ensure that there is at least a minimum number of trips in a given geographic zone.

This still leaves open the possibility that there is a clear path of K trips between two endpoints that are disjointed from the rest of the data set. However, that does not reveal specific destinations. Any location along that path is a potential destination and other potential destinations will have been suppressed.

**Pickups** and **dropoffs** on their own do not leak identifying information, even if they are unique in the data. The geographic zones will be larger than an individual address and if an individual is observed, say, getting picked up, no new information is revealed by showing a pickup in that geographic zone.

## Example Trip Encoded as JSON

This is a protobuf that has been output as JSON. It represents a single trip passing through three geographic zones (0, 1, 2) over two hourly periods (15, 16).
```
{
 "periodSeconds": 3600,
 "cycleLength": 24,
 "geoIds": {
   "0": "-86.723:36.116",
   "1": "-86.722:36.116",
   "2": "-86.722:36.115" },
 "totalTrips": { "15": 1 },
 "totalDistance": { "15": 64.63377380371094 },
 "totalDuration": { "15": 52.599266052246094 },
 "tripVolumes": {
   "15": { "data": { "0": 1 }},
   "16": { "data": { "1": 1, "2": 1 }}
  },
 "pickups": { "15": { "data": { "0": 1 }}},
 "dropoffs": { "16": { "data": { "2": 1 }}},
 "flows": {
   "15": {
   "data": { "0": { "data": { "2": 1 }}}}
  }
}
```

The “tripVolumes” field has two entries for hour 15 and 16. Hour 15 has a single trip count in zone 0, while hour 16 has a count in zones 1 and 2.

The “flows” field shows a trip from zone 0 to zone 2.
