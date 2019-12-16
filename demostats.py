from pb.amms_pb2 import Metrics
import argparse
import google.protobuf.json_format as json_format
import sys

def getspark(series, hi, lo):
    sparkchars = "▁▂▃▄▅▆▇█"
    c = (len(sparkchars)-1)/float(hi-lo)
    return "".join(list(map(lambda x: sparkchars[round((x-lo)*c)], series)))

def sparkline(title, cycle, numerator, denominator=None, units="", precision=0):

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
    if len(series) > 0:
        hi, ave, lo = max(series), sum(series)/len(series), min(series)
        spark = getspark(series, hi, lo)
        print("{title:<18} Min: {min:>6.{precision}f} {units:3} Ave: {ave:>6.{precision}f} {units:3} Max: {max:>6.{precision}f} {units:3}".format(
            title=title, max=hi, ave=ave, min=lo, units=units, precision=precision))
        print("{spark}".format(spark=spark))

def printSparkLines(metrics):
    daily_trips = sum(metrics.total_trips.values())
    print("Period: {} seconds Cycle length: {}".format(metrics.period_seconds, metrics.cycle_length))
    print("Daily trips: {}".format(daily_trips))
    sparkline("Trips by period", metrics.cycle_length, metrics.total_trips)
    sparkline("Average distance", metrics.cycle_length, metrics.total_distance, metrics.total_trips, units="M")
    sparkline("Average duration", metrics.cycle_length, metrics.total_duration, metrics.total_trips, units="s")
    sparkline("Average speed", metrics.cycle_length, metrics.total_distance, metrics.total_duration, units="M/s", precision=2)

def top_n(values, n=5, reverse=True):
    zone_volume = {}
    for hour in values:
        for geo_id in values[hour].data:
            zone_volume[(hour, geo_id)] = values[hour].data[geo_id]
    l = list(zone_volume.items())
    s = sorted(zone_volume.items(), key = lambda x: x[1], reverse=reverse)
    return s[:n]

def printTopTripVolumes(metrics):
    print("Top Trip Volumes")
    print("{:<10}{:<10}{:<10}{:<10}".format("Period", "Lat", "Long", "Count"))
    top_vol = top_n(metrics.trip_volumes, 10)
    for (hour, geo_id), count in top_vol:
        if metrics.geo_ids[geo_id]:
            lat, long = metrics.geo_ids[geo_id].split(":")
            print("{:<10}{:<10}{:<10}{:<10}".format(hour, lat, long, count))

def printSuppressedFlowPercentage(metrics):
    total_flows = 0
    for hour in metrics.flows:
        for pickup in metrics.flows[hour].data:
            for dropoff in metrics.flows[hour].data[pickup].data:
                val = metrics.flows[hour].data[pickup].data[dropoff]
                total_flows += val
    daily_trips = sum(metrics.total_trips.values())
    flow_suppressed_percent = 100 - (100 * float(total_flows) / daily_trips)
    print("Privacy level: {}".format(metrics.privacy_level))
    print("Flows Suppressed: {:2.2f}%".format(flow_suppressed_percent))

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
    printSuppressedFlowPercentage(metrics)

if __name__ == "__main__":
    sys.exit(main())
