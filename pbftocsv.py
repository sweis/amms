from pb.amms_pb2 import Metrics
from datetime import datetime as dt
import argparse
import logging
import sys

log = logging.getLogger()

def outputVolumes(metrics, openedfile):
    openedfile.write("id, pickup_lat, pickup_long, value, start_time\n")
    for period in metrics.trip_volumes:
        start_time = metrics.start_time + (metrics.period_seconds * period)
        geo_ids = metrics.trip_volumes[period].data
        for geo_id in geo_ids:
            geo = metrics.geo_ids[geo_id]
            long, lat = map(float, geo.split(':'))
            val = geo_ids[geo_id]
            openedfile.write("{},{},{},{},{}\n".format(
                geo_id,
                lat,
                long,
                val,
                dt.fromtimestamp(start_time)))

def outputFlows(metrics, openedfile):
    openedfile.write("id, pickup_lat, pickup_long, dropoff_lat, dropoff_long, value, start_time\n")
    for period in metrics.flows:
        start_time = metrics.start_time + (metrics.period_seconds * period)
        pickups = metrics.flows[period].data
        for pickup in pickups:
            pickup_geo = metrics.geo_ids[pickup]
            pickup_long, pickup_lat = map(float, pickup_geo.split(':'))
            dropoffs = pickups[pickup].data
            for dropoff in dropoffs:
                dropoff_geo = metrics.geo_ids[dropoff]
                dropoff_long, dropoff_lat = map(float, dropoff_geo.split(':'))
                val = dropoffs[dropoff]
                openedfile.write("{}->{},{},{},{},{},{},{}\n".format(
                    pickup,
                    dropoff,
                    pickup_lat,
                    pickup_long,
                    dropoff_lat,
                    dropoff_long,
                    val,
                    dt.fromtimestamp(start_time)))

def main():
    parser = argparse.ArgumentParser(
        description='Convert PBF file into a CSV file')
    parser.add_argument(
        'input',
        help='Input PBF filname'
    )
    parser.add_argument(
        'output',
        help='Output CSV prefix [output]-{flow,volume}.csv'
    )
    parser.add_argument(
        '-f',
        '--flow',
        action='store_true',
        default=False,
        help='Output a flow CSV file'
    )
    parser.add_argument(
        '-v',
        '--volume',
        action='store_true',
        default=True,
        help='Output a volume CSV file'
    )
    args = parser.parse_args()
    metrics = Metrics()
    with open(args.input, 'rb') as pbfile:
        metrics.ParseFromString(pbfile.read())

    if args.volume:
        outfilename = "{}-volume.csv".format(args.output)
        log.info("Outputting {}".format(outfilename))
        with open(outfilename, 'w') as volumecsv:
            outputVolumes(metrics, volumecsv)

    if args.flow:
        outfilename = "{}-flow.csv".format(args.output)
        log.info("Outputting {}".format(outfilename))
        with open(outfilename, 'w') as volumecsv:
            outputVolumes(metrics, volumecsv)

if __name__ == "__main__":
    sys.exit(main())
