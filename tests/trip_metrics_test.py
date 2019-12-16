import unittest
import readtrips

class TestPoint:
    def __init__(self, field, indices, value):
        self.field = field
        self.indices = indices
        self.value = value

TEST_VECTOR_24 = [
    TestPoint("geo_ids", [0], "-86.825:36.133"),
    TestPoint("total_trips", [2], 15),
    TestPoint("total_distance",[12], 32191.826171875),
    TestPoint("total_duration", [23], 11986.3046875),
    TestPoint("pickups", [14, 829], 1),
    TestPoint("dropoffs", [8, 1106], 1),
    TestPoint("trip_volumes", [11, 409], 5),
    TestPoint("trip_volumes", [12, 61], 3),
    TestPoint("flows", [18, 283, 47], 1),
    TestPoint("flows", [8, 1308, 1962], 1)
]

TEST_VECTOR_168 = [
    TestPoint("geo_ids", [0], "-86.825:36.133"),
    TestPoint("total_trips", [122], 4),
    TestPoint("total_distance",[105], 3922.567626953125),
    TestPoint("total_duration", [118], 4897.15234375),
    TestPoint("pickups", [93, 75], 1),
    TestPoint("dropoffs", [43, 1369], 1),
    TestPoint("trip_volumes", [72, 691], 4),
    TestPoint("trip_volumes", [66, 2], 3),
    TestPoint("flows", [110, 1167, 914], 1)
]

SUPPRESSED_TEST_VECTOR = TEST_VECTOR_24[:-3]
SUPPRESSED_TEST_VECTOR.extend([
    TestPoint("trip_volumes", [12, 61], 0),
    TestPoint("flows", [18, 283, 47], 0),
    TestPoint("flows", [8, 1308, 1962], 0),
    TestPoint("privacy_level", [], 5)
])

class TripMetricsTest(unittest.TestCase):
    def doTestFields(self, metrics, vector):
        # Spot check several fixed expected values
        for t in vector:
            field = getattr(metrics, t.field)
            for i in t.indices:
                field = field[i]
                if hasattr(field, 'data'):
                    field = getattr(field, 'data')
            self.assertEqual(field, t.value)

    def test_readjson(self):
        metrics = readtrips.metricsFromJSON(
            input_filename = "sampledata/trips.json",
            gpsaccuracy = 3,
            period = 3600,
            cycle_length = 24
        )
        self.doTestFields(metrics, TEST_VECTOR_24)

    def test_readpbf_24_hour_cycle(self):
        metrics = readtrips.metricsFromPBF(
            input_filename = "sampledata/trips-24.pbf",
            gpsaccuracy = 3
        )
        self.doTestFields(metrics, TEST_VECTOR_24)

    def test_readpbf_168_hour_cycle(self):
        metrics = readtrips.metricsFromPBF(
            input_filename = "sampledata/trips-168.pbf",
            gpsaccuracy = 3
        )
        self.doTestFields(metrics, TEST_VECTOR_168)


    def test_suppression(self):
        metrics = readtrips.metricsFromJSON(
            input_filename = "sampledata/trips.json",
            gpsaccuracy = 3,
            period = 3600,
            cycle_length = 24
        )
        suppressed = readtrips.suppress(metrics, 5)
        self.doTestFields(suppressed, SUPPRESSED_TEST_VECTOR)

if __name__ == '__main__':
    unittest.main()
