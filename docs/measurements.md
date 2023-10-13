# Measurement Definitions

## Single Stream Throughput

The maximum AVG FPS for a single stream and single pipeline runner process.

## Stream Density

The maximum number of streams that can be processed at the `target-fps` in parallel.

The `target-fps` can be calculated per stream (all streams must reach
the target) or by overall average (the average FPS over all streams
must reach the target).

## Latency

>Note: Only enabled for dlstreamer runner

>Note: Latency data collection is based on setting `GST_DEBUG_FILE` environment variable but this also sends all GStreamer messages to the same debug log file.

`--measure latency` enables Gstreamer environment variables that generates a latency log per stream.

The values reported in results.json corresponds to `Latency` of each stream and elements and also aggregate latency of all streams and elements.

- latency: Pipeline(s) latency in ms
- avg: Average frame latency in ms
- min: Minimum frame latency in ms
- max: Maximum frame latency in ms
- element: Name of the element

```json
        "streams_latency": [
            {
                "latency": 59.728906,
                "avg": 7214.50768,
                "min": 1014.717139,
                "max": 16405.333814,
                "elements": {
                    "gvafpscounter0": {
                        "element": "gvafpscounter0",
                        "avg": 0.065006,
                        "min": 0.007996,
                        "max": 1.355887
                    },
                    "gvametapublish0": {
                        "element": "gvametapublish0",
                        "avg": 0.05034,
                        "min": 0.008553,
                        "max": 1.470156
                    },
                    "gvametaconvert0": {
                        "element": "gvametaconvert0",
                        "avg": 0.265534,
                        "min": 0.1008,
                        "max": 3.995186
                    },
                    "classify": {
                        "element": "classify",
                        "avg": 121.31424,
                        "min": 32.663941,
                        "max": 1179.01843
                    },
                    "decode0": {
                        "element": "decode0",
                        "avg": 537.91149,
                        "min": 44.248252,
                        "max": 2627.100483
                    },
                    "detect0": {
                        "element": "detect0",
                        "avg": 220.594223,
                        "min": 16.387482,
                        "max": 1650.571281
                    },
                    "capsfilter1": {
                        "element": "capsfilter1",
                        "avg": 0.213961,
                        "min": 0.010574,
                        "max": 3.824142
                    },
                    "h264parse0": {
                        "element": "h264parse0",
                        "avg": 6123.784377,
                        "min": 0.040247,
                        "max": 15279.107168
                    }
                }
            },
            {
                "latency": 59.936533,
                "avg": 7250.257895,
                "min": 1037.520897,
                "max": 16541.911277,
                "elements": {
                    "decode0": {
                        "element": "decode0",
                        "avg": 540.458506,
                        "min": 44.237913,
                        "max": 2611.02045
                    },
                    "detect0": {
                        "element": "detect0",
                        "avg": 220.600748,
                        "min": 29.014099,
                        "max": 1339.557634
                    },
                    "capsfilter1": {
                        "element": "capsfilter1",
                        "avg": 0.025136,
                        "min": 0.007977,
                        "max": 0.555619
                    },
                    "h264parse0": {
                        "element": "h264parse0",
                        "avg": 6144.647523,
                        "min": 0.028712,
                        "max": 15238.210297
                    },
                    "classify": {
                        "element": "classify",
                        "avg": 289.660346,
                        "min": 198.632705,
                        "max": 1973.208619
                    },
                    "gvafpscounter0": {
                        "element": "gvafpscounter0",
                        "avg": 0.012865,
                        "min": 0.008176,
                        "max": 0.153171
                    },
                    "gvametapublish0": {
                        "element": "gvametapublish0",
                        "avg": 0.021014,
                        "min": 0.009431,
                        "max": 1.092253
                    },
                    "gvametaconvert0": {
                        "element": "gvametaconvert0",
                        "avg": 0.196004,
                        "min": 0.130687,
                        "max": 1.337195
                    }
                }
            }
        ],
        "aggregate_latency": {
            "pipeline(s)": {
                "latency": 29.916359749999998,
                "avg": 7232.3827875,
                "min": 1014.717139,
                "max": 16541.911277
            },
            "elements": {
                "gvafpscounter0": {
                    "element": "gvafpscounter0",
                    "min": 0.007996,
                    "max": 1.355887,
                    "avg": 0.0389355
                },
                "gvametapublish0": {
                    "element": "gvametapublish0",
                    "min": 0.008553,
                    "max": 1.470156,
                    "avg": 0.035677
                },
                "gvametaconvert0": {
                    "element": "gvametaconvert0",
                    "min": 0.1008,
                    "max": 3.995186,
                    "avg": 0.230769
                },
                "classify": {
                    "element": "classify",
                    "min": 32.663941,
                    "max": 1973.208619,
                    "avg": 205.487293
                },
                "decode0": {
                    "element": "decode0",
                    "min": 44.237913,
                    "max": 2627.100483,
                    "avg": 539.184998
                },
                "detect0": {
                    "element": "detect0",
                    "min": 16.387482,
                    "max": 1650.571281,
                    "avg": 220.5974855
                },
                "capsfilter1": {
                    "element": "capsfilter1",
                    "min": 0.007977,
                    "max": 3.824142,
                    "avg": 0.1195485
                },
                "h264parse0": {
                    "element": "h264parse0",
                    "min": 0.028712,
                    "max": 15279.107168,
                    "avg": 6134.21595
                }
            }
        }
```