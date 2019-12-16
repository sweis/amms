from pb.amms_pb2 import Metrics
import argparse
import google.protobuf.json_format as json_format
import sys

def getParser():
    parser = argparse.ArgumentParser(
        description='Aggregate MDS trip data into a TripMetrics protocol buffer')
    parser.add_argument(
        'input_filename',
        help='Input PBF filname'
    )
    parser.add_argument(
        '--output_filename',
        help='Output JSON filename. If not provided, output will be printed.')
    return parser

def main():
    parser = getParser()
    args = parser.parse_args()
    metrics = Metrics()
    with open(args.input_filename, 'rb') as pbfile:
        metrics.ParseFromString(pbfile.read())
    json = json_format.MessageToJson(metrics)
    if args.output_filename:
        with open(args.output_filename, 'w') as jsonfile:
            jsonfile.write(json)
    else:
        print(json)

if __name__ == "__main__":
    sys.exit(main())
