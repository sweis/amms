from pb.amms_pb2 import Metrics
from datetime import datetime as dt
import argparse
import google.protobuf.json_format as json_format
import readtrips
import sys

def getspark(series, hi, lo):
    sparkchars = "▁▂▃▄▅▆▇█"
    c = (len(sparkchars)-1)/float(hi-lo) if hi != lo else len(sparkchars)/2
    return "".join(list(map(lambda x: sparkchars[round((x-lo)*c)], series)))

def sparkline(title, cycle, numerator, denominator=None, units="", precision=0):
    if not numerator:
        return
    series = []
    for k in range(0, cycle):
        if denominator:
            if k in numerator and denominator[k]:
                series.append(float(numerator[k])/denominator[k])
            else:
                series.append(0)
        else:
            if k in numerator and numerator[k]:
                series.append(numerator[k])
            else:
                series.append(0)
    sumval, hi, ave, lo = sum(series), max(series), sum(series)/len(series), min(series)
    spark = getspark(series, hi, lo)
    print("{title:<18} Min: {min:>6.{precision}f} {units:3} Ave: {ave:>6.{precision}f} {units:3} Max: {max:>6.{precision}f} {units:3} Sum: {sum:>6.{precision}f}".format(
        sum=sumval, title=title, max=hi, ave=ave, min=lo, units=units, precision=precision))
    print("{spark}".format(spark=spark))

def top_n(values, n=5, reverse=True):
    zone_volume = {}
    for hour in values:
        for geo_id in values[hour].data:
            zone_volume[(hour, geo_id)] = values[hour].data[geo_id]
    l = list(zone_volume.items())
    s = sorted(zone_volume.items(), key = lambda x: x[1], reverse=reverse)
    return s[:n]

def getTotalByPeriod(metrics, field_name):
    output_series = []
    field = getattr(metrics, field_name)
    for period in field:
        tally = 0
        for pickup in field[period].data:
            v = field[period].data[pickup]
            if hasattr(v, "data"):
                for dropoff in v.data:
                    tally += v.data[dropoff]
            else:
                tally += v
        output_series.append((period, tally))
    return dict(output_series)

def printSparkLines(metrics):
    daily_trips = sum(metrics.total_trips.values())
    trip_volume_by_period = getTotalByPeriod(metrics, 'trip_volumes')
    flows_by_period = getTotalByPeriod(metrics, 'flows')
    available_by_period = getTotalByPeriod(metrics, 'availability')
    on_street_by_period = getTotalByPeriod(metrics, 'on_street')

    print("Total trips: {}".format(daily_trips))
    print("Start: {}".format(dt.fromtimestamp(metrics.start_time)))
    print("End: {}".format(dt.fromtimestamp(metrics.end_time)))
    print("Period: {} seconds".format(metrics.period_seconds))
    print("Cycle length: {}".format(metrics.cycle_length))

    trip_volume_by_period = getTotalByPeriod(metrics, 'trip_volumes')
    total_trip_volume = sum(trip_volume_by_period.values())
    flows_by_period = getTotalByPeriod(metrics, 'flows')
    total_flows = sum(flows_by_period.values())
    print("Privacy: {}".format(metrics.privacy_level))
    print("Volume Suppressed: {}\tTotal Volume: {}".format(metrics.trip_volume_suppressed, total_trip_volume))
    print("Flow Suppressed: {}\tTotal Flows: {}".format(metrics.flows_suppressed, total_flows))
    sparkline("Trips by period", metrics.cycle_length, metrics.total_trips)
    sparkline("Average distance", metrics.cycle_length, metrics.total_distance, metrics.total_trips, units="M")
    sparkline("Average duration", metrics.cycle_length, metrics.total_duration, metrics.total_trips, units="s")
    sparkline("Average speed", metrics.cycle_length, metrics.total_distance, metrics.total_duration, units="M/s", precision=2)
    sparkline("Trip Volume", metrics.cycle_length, trip_volume_by_period)
    sparkline("Flows", metrics.cycle_length, flows_by_period)
    sparkline("Availability", metrics.cycle_length, available_by_period)
    sparkline("On Street", metrics.cycle_length, on_street_by_period)

def printTopTripVolumes(metrics):
    print("Top Trip Volumes")
    print("{:<10}{:<10}{:<10}{:<10}".format("Period", "Lat", "Long", "Count"))
    top_vol = top_n(metrics.trip_volumes, 10)
    for (hour, geo_id), count in top_vol:
        if metrics.geo_ids[geo_id]:
            lat, long = metrics.geo_ids[geo_id].split(":")
            print("{:<10}{:<10}{:<10}{:<10}".format(hour, lat, long, count))

def printPrivacySuppressionStats(metrics, privacy_levels):
    print("Privacy Flow Suppression")
    print("{:>15}{:>15}{:>8}{:>15}{:>8}".format(
        "Privacy Level", "Supp. Volume", "%", "Supp. Flows", "%"))
    trip_volume_by_period = getTotalByPeriod(metrics, 'trip_volumes')
    total_trip_volume = sum(trip_volume_by_period.values())
    flows_by_period = getTotalByPeriod(metrics, 'flows')
    total_flows = sum(flows_by_period.values())
    for privacy_level in privacy_levels:
        suppressed = readtrips.suppress(metrics, privacy_level)
        percent_volume_suppressed = 100*(float(suppressed.trip_volume_suppressed)/total_trip_volume) if total_trip_volume else 0
        percent_flows_suppressed = 100*(float(suppressed.flows_suppressed)/total_flows) if total_flows else 0

        print("{:>15}{:>15}{:>8.2f}{:>15}{:>8.2f}".format(
            privacy_level,
            suppressed.trip_volume_suppressed,
            percent_volume_suppressed,
            suppressed.flows_suppressed,
            percent_flows_suppressed)
        )

def main():
    parser = argparse.ArgumentParser(
        description='Aggregate MDS trip data into a Metrics protocol buffer')
    parser.add_argument(
        'input_filename',
        help='Input PBF filname'
    )
    args = parser.parse_args()
    metrics = Metrics()
    with open(args.input_filename, 'rb') as pbfile:
        metrics.ParseFromString(pbfile.read())
    printSparkLines(metrics)
    print()
    printTopTripVolumes(metrics)
    print()
    printPrivacySuppressionStats(metrics, [1, 2, 3, 4, 5])

if __name__ == "__main__":
    sys.exit(main())
