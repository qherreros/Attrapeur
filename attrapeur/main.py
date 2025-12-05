import argparse
from time import sleep
from typing import Any

from googleapiclient import discovery  # type: ignore
from loguru import logger
from notifypy import Notify  # type: ignore


def get_instance_status(service: Any, zone: str, instance: str):
    project = "elastic-ml"
    request = service.instances().get(project=project, zone=zone, instance=instance)
    return request.execute()["status"]


def start_instance(service: Any, zone: str, instance: str):
    project = "elastic-ml"
    request = service.instances().start(project=project, zone=zone, instance=instance)
    return request.execute()


def notify(title: str, message: str):
    notification = Notify()
    notification.title = title
    notification.message = message
    notification.send()


def main(instance: str, zone: str):
    logger.info(f"Starting instance {instance} in zone {zone}")

    PENDING_STATES = {"PROVISIONING", "STAGING"}

    service = discovery.build("compute", "v1")
    start_instance(service, zone, instance)

    counter = 0
    is_started = False
    while not is_started:
        status = get_instance_status(service, zone, instance)

        if status == "RUNNING":
            is_started = True
            logger.info("Instance started")
            notify("Instance started", f"{instance} has been started on GCP")
        elif status in PENDING_STATES:
            logger.info(f"Instance is still in {status} state. Extending wait time...")
        elif counter > 30:
            logger.warning(f"Instance not started (Status: {status}). Trying again...")
            start_instance(service, zone, instance)
            counter = 0
        else:
            counter += 1
        sleep(5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Start a GCP instance.")
    parser.add_argument("-z", "--zone")
    parser.add_argument("-i", "--instance")
    args = parser.parse_args()

    main(args.instance, args.zone)
