def pytest_addoption(parser):
    parser.addoption("--pipeline",action="append",choices=["smoke","nightly","od-h264-mbnetssd","od-h264-yolov3"],dest="pipelines",default=[])


def pytest_generate_tests(metafunc):
    pipelines = metafunc.config.getoption("pipelines")
    if ("smoke" in pipelines) or (not pipelines):
        if "smoke" in pipelines: pipelines.remove("smoke")
        pipelines.extend(["od-h264-mbnetssd"])
    elif ("nightly" in pipelines):
        pipelines.remove("nightly")
        pipelines.extend(["od-h264-yolov3","od-h264-mbnetssd"])
    if "pipeline" in metafunc.fixturenames:
        metafunc.parametrize("pipeline", pipelines)
