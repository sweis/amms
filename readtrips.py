from pb.amms_pb2 import Metrics

import argparse
import datetime as dt
import json
import jsonschema
import logging
import pandas as pd
import sys

log = logging.getLogger()

def getPeriod(seconds, period, cycle_length):
    # This will bucket seconds into whatever time period is specified, e.g.
    # 3600 seconds will be hourly. It will then aggregate based on a cycle
    # length, e.g. hours of the week.
    return int(seconds/period) % cycle_length

def latLongToZone(geo_ids, lat, long, gpsaccuracy, inverse_geo_ids):
    coordformat = "{lat:03.{gpsaccuracy}f}:{long:03.{gpsaccuracy}f}".format(
        lat=lat, long=long, gpsaccuracy=gpsaccuracy)
    coordinates = coordformat.format(lat, long)
    if coordinates not in inverse_geo_ids:
        geo_id_count = len(geo_ids)
        inverse_geo_ids[coordinates] = geo_id_count
        geo_ids[geo_id_count] = coordinates
    return inverse_geo_ids[coordinates]

def metricsFromPBF(input_filename, period=None, cycle_length=None, gpsaccuracy=None):
    with open(input_filename, 'rb') as pbfile:
        metrics = Metrics()
        metrics.ParseFromString(pbfile.read())
        return metrics

def metricsFromCSV(input_filename, period, cycle_length, gpsaccuracy):
    df = pd.read_csv(input_filename,
        sep='\\s*,\\s*',
        engine='python',
        parse_dates=[['pickup_date', 'pickup_time'],['dropoff_date', 'dropoff_time']])
    metrics = Metrics()
    metrics.period_seconds = period
    metrics.cycle_length = cycle_length
    count = 0
    inverse_geo_ids = {}
    for k, v in df.iterrows():
        start_time = v['pickup_date_pickup_time']
        end_time = v['dropoff_date_dropoff_time']
        start_period = getPeriod(start_time.timestamp(), metrics.period_seconds, metrics.cycle_length)
        end_period = getPeriod(end_time.timestamp(), metrics.period_seconds, metrics.cycle_length)
        metrics.total_trips[start_period] += 1
        metrics.total_duration[start_period] += pd.Timedelta(end_time - start_time).seconds
        pickup = latLongToZone(metrics.geo_ids,
            v['pickup_lat'],
            v['pickup_long'],
            gpsaccuracy,
            inverse_geo_ids)
        dropoff = latLongToZone(metrics.geo_ids,
            v['dropoff_lat'],
            v['dropoff_long'],
            gpsaccuracy,
            inverse_geo_ids)
        metrics.pickups[start_period].data[pickup] += 1
        metrics.dropoffs[end_period].data[dropoff] += 1
        metrics.flows[start_period].data[pickup].data[dropoff] += 1
        count += 1
    logging.debug("Read {} trips".format(count))
    return metrics

def metricsFromJSON(input_filename, period, cycle_length, gpsaccuracy):
    metrics = Metrics()
    metrics.period_seconds = period
    metrics.cycle_length = cycle_length
    count = 0
    inverse_geo_ids = {}
    with open(input_filename) as f:
        for trip in map(json.loads, f.readlines()):
            count += 1
            start_period = getPeriod(trip['start_time'], metrics.period_seconds, metrics.cycle_length)
            duration = float(trip['trip_duration'])
            distance = float(trip['trip_distance'])
            metrics.total_trips[start_period] += 1
            metrics.total_duration[start_period] += duration
            metrics.total_distance[start_period] += distance
            pickup = None
            dropoff = None
            for route_point in trip['route']['features']:
                period = getPeriod(route_point['properties']['timestamp'], metrics.period_seconds, metrics.cycle_length)
                (lat, long) = map(float, route_point['geometry']['coordinates'])
                geo_id = latLongToZone(metrics.geo_ids, lat, long, gpsaccuracy, inverse_geo_ids)
                metrics.trip_volumes[period].data[geo_id] += 1
                if pickup == None:
                    # The first entry in the geometry is assumed to be the pickup)
                    pickup = geo_id
                # The lat entry in the geometry is assumed to be the dropoff
                end_period = period
                dropoff = geo_id
            metrics.pickups[start_period].data[pickup] += 1
            metrics.dropoffs[end_period].data[dropoff] += 1
            # Flows will be indexed by their start period
            metrics.flows[start_period].data[pickup].data[dropoff] += 1
    logging.debug("Read {} trips".format(count))
    return metrics

def parseChanges(metrics, changes_filename, period, cycle_length, gpsaccuracy):
    if not metrics:
        metrics = Metrics()
        metrics.period_seconds = period
        metrics.cycle_length = cycle_length
    count = 0
    availability_map = {}
    onstreet_map = {}
    inverse_geo_ids = dict([(x[1], x[0]) for x in metrics.geo_ids.items()])
    with open(changes_filename) as f:
        for change in map(json.loads, f.readlines()):
            count += 1
            event_period = getPeriod(change['event_time'], metrics.period_seconds, metrics.cycle_length)
            vehicle_id = change['vehicle_id']
            event_type = change['event_type']
            (lat, long) = map(float, change['event_location']['geometry']['coordinates'])
            geo_id = latLongToZone(
                metrics.geo_ids,
                lat,
                long,
                gpsaccuracy,
                inverse_geo_ids)

            if event_period not in onstreet_map:
                onstreet_map[event_period] = {}
            if geo_id not in onstreet_map[event_period]:
                onstreet_map[event_period][geo_id] = {}
            if vehicle_id not in onstreet_map[event_period][geo_id]:
                onstreet_map[event_period][geo_id][vehicle_id] = 0
            onstreet_map[event_period][geo_id][vehicle_id] += 1

            if event_type == "available":
                if event_period not in availability_map:
                    availability_map[event_period] = {}
                if geo_id not in availability_map[event_period]:
                    availability_map[event_period][geo_id] = {}
                if vehicle_id not in availability_map[event_period][geo_id]:
                    availability_map[event_period][geo_id][vehicle_id] = 0
                availability_map[event_period][geo_id][vehicle_id] += 1
    for period in availability_map:
        for geo_id in availability_map[period]:
            metrics.availability[period].data[geo_id] = len(availability_map[period][geo_id])
    for period in onstreet_map:
        for geo_id in onstreet_map[period]:
            metrics.on_street[period].data[geo_id] = len(onstreet_map[period][geo_id])
    logging.debug("Read {} vehicle changes".format(count))
    return metrics

def outputFile(metrics, output_filename):
    logging.debug("Writing to {}".format(output_filename))
    with open(output_filename, "wb") as output:
        output.write(metrics.SerializeToString())

def decompose(degree, source_graph, dest_graph, degrees):
    if degree not in degrees:
        degrees[degree] = []
    to_remove = []
    for source in source_graph:
        out_degree = len(source_graph[source])
        if out_degree <= degree:
            degrees[degree].append(source)
            to_remove.append(source)
            # Delete this node and its edges
            for dest in source_graph[source]:
                dest_graph[dest].remove(source)
    removed = len(to_remove)
    for source in to_remove:
        del source_graph[source]
    return removed

def graphToEdgeSet(graph, reverse=False):
    edges = []
    for source in graph:
        for dest in graph[source]:
            if reverse:
                edges.append((dest, source))
            else:
                edges.append((source, dest))
    return set(edges)

def decomposeTrips(pickups, privacy_level):
    # Set up edge adjacency lists
    outbound = {}
    inbound = {}
    for pickup in pickups:
        dropoffs = pickups[pickup].data
        if pickup not in outbound:
            outbound[pickup] = []
        for dropoff in dropoffs:
            if dropoff not in outbound[pickup]:
                outbound[pickup].append(dropoff)
            if dropoff not in inbound:
                inbound[dropoff] = []
            if pickup not in inbound[dropoff]:
                inbound[dropoff].append(pickup)
    out_degrees = {}
    in_degrees = {}
    degree, out_removed, in_removed = 1, 0, 0
    for degree in range(1, privacy_level):
        out_removed = decompose(degree, outbound, inbound, out_degrees)
        in_removed = decompose(degree, inbound, outbound, in_degrees)
        if out_removed == 0 and in_removed == 0:
            break
        degree += 1
    # Check that all the edges are consistent in outbound and inbound graphs
    outedges = graphToEdgeSet(outbound)
    inedges = graphToEdgeSet(inbound, reverse=True)
    assert not outedges.symmetric_difference(inedges)
    return outedges

def suppress(metrics, privacy_level):
    logging.debug("Suppressing flows with l-diversity of {}".format(privacy_level))
    suppressed_metrics = Metrics()
    suppressed_metrics.MergeFrom(metrics)
    suppressed_metrics.privacy_level = privacy_level
    suppressed_metrics.ClearField("trip_volumes")
    suppressed_metrics.ClearField("flows")

    # Enforce k-anonymity of trip volumes
    for period in metrics.trip_volumes:
        geo_ids = metrics.trip_volumes[period].data
        for geo_id in geo_ids:
            count = metrics.trip_volumes[period].data[geo_id]
            if count >= suppressed_metrics.privacy_level:
                suppressed_metrics.trip_volumes[period].data[geo_id] = count

    # Enforce l-diversity of flows
    for period in metrics.flows:
        pickups = metrics.flows[period].data
        trips = decomposeTrips(metrics.flows[period].data, privacy_level)
        # Copy over flow data from the suppressed pickup/dropoff pairs
        for (pickup, dropoff) in trips:
            suppressed_metrics.flows[period].data[pickup].data[dropoff] = pickups[pickup].data[dropoff]
    return suppressed_metrics

def getParser():
    parser = argparse.ArgumentParser(
        description='Aggregate MDS trip data into a Metrics protocol buffer')
    parser.add_argument(
        'input_trips',
        help='Input trips filname. Must end with .json, .csv., or .pbf'
    )
    parser.add_argument(
        '--changes_filename',
        help='Input file with vehicle changes. Must end with .json')
    parser.add_argument(
        '--period',
        default=3600,
        type=int,
        help='Time period in seconds. Hour by default.'
    )
    parser.add_argument(
        '--cycle_length',
        default=168,
        type=int,
        help='The number of periods in a cycle. If provided, periods '
             'will be aggregated on a cycle, e.g. the same hour of a day will '
             'be tallied.'
    )
    parser.add_argument(
        '--output_filename',
        default="output.pbf",
        help='Output filename')
    parser.add_argument(
        '--suppress',
        action='store_true',
        default=True,
        help='Output suppressed flows subject to k-anonymity')
    parser.add_argument(
        '--suppress_prefix',
        default="suppress",
        help='Output filename prefix for suppressed flows. [prefix]-[k].pbf')
    parser.add_argument(
        '--accuracy',
        default=3,
        type=int,
        help='Decimal digits of GPS accuracy used for zones')
    parser.add_argument(
        '--privacy',
        default=5,
        type=int,
        help='k-anonymity or l-diversity for suppressed output')
    return parser

def main():
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    parser = getParser()
    args = parser.parse_args()

    if args.input_trips.endswith('pbf'):
        parsingFunction = metricsFromPBF
    elif args.input_trips.endswith('csv'):
        parsingFunction = metricsFromCSV
    elif args.input_trips.endswith('json'):
        parsingFunction = metricsFromJSON

    logging.debug("Reading {}".format(args.input_trips))
    metrics = parsingFunction(args.input_trips, args.period, args.cycle_length, args.accuracy)
    if args.changes_filename:
        metrics = parseChanges(metrics, args.changes_filename, args.period, args.cycle_length, args.accuracy)
    outputFile(metrics, args.output_filename)
    if args.suppress:
        suppressed = suppress(metrics, args.privacy)
        suppressed_filename = "{}-{}.pbf".format(args.suppress_prefix, args.privacy)
        outputFile(suppressed, suppressed_filename)

if __name__ == "__main__":
    sys.exit(main())
