from pb.amms_pb2 import Metrics
import argparse
import google.protobuf.json_format as json_format
import readtrips
import sys

def getspark(series, hi, lo):
    sparkchars = "▁▂▃▄▅▆▇█"
    c = (len(sparkchars)-1)/float(hi-lo)
    return "".join(list(map(lambda x: sparkchars[round((x-lo)*c)], series)))

def sparkline(title, cycle, numerator, denominator=None, units="", precision=0):
    if not numerator:
        return
    spark = ""
    series = []
    for k in sorted(numerator):
        if denominator:
            if denominator[k]:
                series.append(float(numerator[k])/denominator[k])
            else:
                series.append(0)
        else:
            series.append(numerator[k])
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

def getTotalByPeriod(metrics, flow=False):
    output_series = []
    for period in metrics.flows:
        tally = 0
        for pickup in metrics.flows[period].data:
            if flow:
                for dropoff in metrics.flows[period].data[pickup].data:
                    tally += metrics.flows[period].data[pickup].data[dropoff]
            else:
                tally += metrics.trip_volumes[period].data[pickup]
        output_series.append((period, tally))
    return dict(output_series)

def printSparkLines(metrics):
    daily_trips = sum(metrics.total_trips.values())
    print("Period: {} seconds Cycle length: {}".format(metrics.period_seconds, metrics.cycle_length))
    print("Daily trips: {}".format(daily_trips))
    sparkline("Trips by period", metrics.cycle_length, metrics.total_trips)
    sparkline("Average distance", metrics.cycle_length, metrics.total_distance, metrics.total_trips, units="M")
    sparkline("Average duration", metrics.cycle_length, metrics.total_duration, metrics.total_trips, units="s")
    sparkline("Average speed", metrics.cycle_length, metrics.total_distance, metrics.total_duration, units="M/s", precision=2)

def printTopTripVolumes(metrics):
    print("Top Trip Volumes")
    print("{:<10}{:<10}{:<10}{:<10}".format("Period", "Lat", "Long", "Count"))
    top_vol = top_n(metrics.trip_volumes, 10)
    for (hour, geo_id), count in top_vol:
        if metrics.geo_ids[geo_id]:
            lat, long = metrics.geo_ids[geo_id].split(":")
            print("{:<10}{:<10}{:<10}{:<10}".format(hour, lat, long, count))

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
    trips_by_period = getTotalByPeriod(metrics, flow=False)
    total_trip_volume = sum(trips_by_period.values())
    sparkline("Trip Volume", metrics.cycle_length, trips_by_period)
    print()
    flows_by_period = getTotalByPeriod(metrics, flow=True)
    total_flows = sum(flows_by_period.values())
    sparkline("Flows", metrics.cycle_length, flows_by_period)
    print()
    printTopTripVolumes(metrics)
    print()
    privacy_levels = [1, 2, 3, 4, 5]
    print("Privacy Flow Suppression")
    print("{:<20}{:<20}{:<20}{:<20}{:<20}".format(
        "Privacy Level", "Trip Volume", "% Volume Suppressed", "Flows", "% Flows Suppressed"))
    for privacy_level in privacy_levels:
        suppressed = readtrips.suppress(metrics, privacy_level)
        suppressed_flows_by_period = getTotalByPeriod(suppressed, flow=True)
        suppressed_volume_by_period = getTotalByPeriod(suppressed, flow=False)
        total_suppressed_flows = sum(suppressed_flows_by_period.values())
        total_suppressed_volume = sum(suppressed_volume_by_period.values())
        percent_flows_suppressed = 100*(1.0-(total_suppressed_flows/total_flows)) if total_flows else 0
        percent_volume_suppressed = 100*(1.0-(total_suppressed_volume/total_trip_volume)) if total_trip_volume else 0
        print("{:<20}{:<20}{:<20.2f}{:<20}{:<20.2f}".format(
            privacy_level, total_suppressed_volume, percent_volume_suppressed, total_suppressed_flows, percent_flows_suppressed))

if __name__ == "__main__":
    sys.exit(main())
