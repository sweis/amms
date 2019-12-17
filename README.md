# Aggregated Mobility Metrics Schema

## Overview
The Aggregate Mobility Metrics Schema (AMMS) specifies a portable, compact schema for sharing aggregated mobility data with cities. At a high-level, AMMS allows one to define arbitrary geographic zones and aggregate data by arbitrary time periods and
cycles by zone. AMMS also supports a privacy level, which may be used as a
k-anonymity or l-diversity level to apply to different aggregated metrics.

The schema includes:
* Total trips, distance, & duration by time period
* Pickups & drop-offs by time period & zone
* Trip volumes by time period & zone, with arbitrary k-anonymity
* Flows by time period, pickup, and drop-off zones, with arbitrary l-diversity
* Optionally, vehicle availability and on-street counts by time period & zone.

AMMS is specified as a Protocol Buffer, which provides a portable binary format supporting major languages and easy conversion to JSON. AMMS is input agnostic
and compatible with Mobility Data Specification (MDS) JSON input. An AMMS
protocol buffer output is typical than 1% of the size of the raw MDS input data.

## Building Python Sample Code

`make` will run `protoc --python_out=pb/ amms.proto` and run the unit tests under the `tests/` directory.

### Dependencies
* python3
* protobuf, e.g. `brew install protobuf`

## Demo Python Code Usage

### readtrips.py

`readtrips` will read a trips file in either JSON, CSV, or PBF (protobuf) format
and output as a PBF file. It will optionally suppress data using the given
`--privacy` parameter.

Currently, `readtrips` will map GPS coordinates
to zones by rounding coordinates to 3 decimal digits by default, which is
configurable by the `--accuracy` parameter.

`readtrips` also supports optionally reading an MDS vehicle change file, which
is specified by the `--changes_filename` flag. See `sampledata/tiny-{trips, changes}.json` as example inputs and `sampledata/tiny-trips.pbf` as a sample
output.

#### Usage
```
$ python3 readtrips.py -h
usage: readtrips.py [-h] [--changes_filename CHANGES_FILENAME]
                    [--period PERIOD] [--cycle_length CYCLE_LENGTH]
                    [--output_filename OUTPUT_FILENAME] [--suppress]
                    [--suppress_prefix SUPPRESS_PREFIX] [--accuracy ACCURACY]
                    [--privacy PRIVACY]
                    input_trips

Aggregate MDS trip data into a Metrics protocol buffer

positional arguments:
  input_trips           Input trips filname. Must end with .json, .csv., or
                        .pbf

optional arguments:
  -h, --help            show this help message and exit
  --changes_filename CHANGES_FILENAME
                        Input file with vehicle changes. Must end with .json
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
$ python3 demostats.py sampledata/big-trips-24.pbf
Period: 3600 seconds Cycle length: 24
Daily trips: 104321
Trips by period    Min:   4229     Ave:   4347     Max:   4435     Sum: 104321
▂▆▅█▅▆█▇▇▃▁▆▇▂▆▄▂▇▃▇▄▂▆▆
Average distance   Min:   1040 M   Ave:   1064 M   Max:   1083 M   Sum:  25543
▄▆▃▇▅▄▆▄▄▅█▅▄▄█▄▁▄▇█▃▆▄▇
Average duration   Min:    739 s   Ave:    758 s   Max:    772 s   Sum:  18184
▄▅▄▆▅▄▆▄▄▅█▅▄▄█▄▁▄▆▇▄▆▄▇
Average speed      Min:   1.40 M/s Ave:   1.40 M/s Max:   1.41 M/s Sum:  33.71
▁▅▁▅▆▄▂▇▆▅▂▃▃▃▅█▅▅▅▅▂▁▄▃
Trip Volume        Min: 109913     Ave: 112459     Max: 113694     Sum: 2699006
▄▄▇▇▆▇▆▇▆▆▆▅▆▅█▄▆█▇▇▆▁▆▃
Flows              Min:   4229     Ave:   4347     Max:   4435     Sum: 104321
▂▆▅█▅▆█▇▇▃▁▆▇▂▆▄▂▇▃▇▄▂▆▆

Top Trip Volumes
Period    Lat       Long      Count
14        -86.777   36.167    2115
6         -86.777   36.167    2109
13        -86.777   36.167    2082
7         -86.777   36.167    2078
15        -86.777   36.167    2033
20        -86.777   36.167    2013
8         -86.777   36.167    2006
21        -86.777   36.167    2006
5         -86.777   36.167    1988
12        -86.777   36.167    1983

Privacy Flow Suppression
Privacy Level       Trip Volume         % Volume Suppressed Flows               % Flows Suppressed
1                   2699006             0.00                104321              0.00
2                   2483883             7.97                91186               12.59
3                   2221598             17.69               75902               27.24
4                   1938583             28.17               61703               40.85
5                   1679115             37.79               49594               52.46
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
