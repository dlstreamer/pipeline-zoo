def pytest_addoption(parser):
    parser.addoption("--pipeline",action="append",choices=["smoke","nightly","od-h264-mbnetssd","od-h264-yolov3","od-h264-person-vehicle-bike","od-h264-ssd-mobilenet-v1-coco","decode-h265"],
                     dest="pipelines",default=[])


def pytest_generate_tests(metafunc):
    pipelines = metafunc.config.getoption("pipelines")
    if ("smoke" in pipelines) or (not pipelines):
        if "smoke" in pipelines: pipelines.remove("smoke")
        pipelines.extend(["od-h264-person-vehicle-bike"])
    elif ("nightly" in pipelines):
        pipelines.remove("nightly")
        pipelines.extend(["od-h264-yolov3","od-h264-person-vehicle-bike","decode-h265","oc-h264-full_frame-resnet-50-tf", "od-h264-ssd-mobilenet-v1-coco"])
    if "pipeline" in metafunc.fixturenames:
        metafunc.parametrize("pipeline", pipelines)
