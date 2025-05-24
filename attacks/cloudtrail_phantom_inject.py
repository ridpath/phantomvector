import json
import logging
import random
import os
import time
from datetime import datetime, timedelta
from typing import List, Optional
from faker import Faker

logger = logging.getLogger("CloudTrailPhantom")
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

fake = Faker()

SEVERITY_TAGS = [
    "malware_analysis",
    "privilege_escalation",
    "c2_beacon_init",
    "exfil_staging",
    "rce_lambda_abuse"
]

REGIONS = [
    "us-east-1", "us-west-2", "eu-central-1", "ap-southeast-2"
]

def _generate_phantom_event(lambda_name: str, region: str = None, severity: str = None) -> dict:
    """
    Generate a valid CloudTrail log entry for a non-existent Lambda.
    """
    region = region or random.choice(REGIONS)
    severity = severity or random.choice(SEVERITY_TAGS)

    ts = datetime.utcnow() - timedelta(seconds=random.randint(30, 300))

    event = {
        "eventVersion": "1.08",
        "userIdentity": {
            "type": "IAMUser",
            "principalId": fake.uuid4(),
            "arn": f"arn:aws:iam::{random.randint(100000000000,999999999999)}:user/{fake.user_name()}",
            "accountId": str(random.randint(100000000000,999999999999)),
            "accessKeyId": fake.sha1()[:20],
            "userName": fake.user_name()
        },
        "eventTime": ts.isoformat() + "Z",
        "eventSource": "lambda.amazonaws.com",
        "eventName": "Invoke",
        "awsRegion": region,
        "sourceIPAddress": fake.ipv4_public(),
        "userAgent": random.choice([
            "aws-cli/2.7.20", "Boto3/1.24.28", "Go-http-client/1.1", "CloudShell", "kubectl/v1.25"
        ]),
        "requestParameters": {
            "functionName": lambda_name,
            "invocationType": "Event"
        },
        "responseElements": {
            "statusCode": 202,
            "requestId": fake.uuid4()
        },
        "requestID": fake.uuid4(),
        "eventID": fake.uuid4(),
        "readOnly": False,
        "eventType": "AwsApiCall",
        "managementEvent": True,
        "recipientAccountId": str(random.randint(100000000000,999999999999)),
        "eventCategory": "Management",
        "additionalEventData": {
            "severityTag": severity,
            "phantom": True
        }
    }

    return event


def generate_phantom_log_batch(
    count: int = 10,
    prefix: str = "phantom-lambda-",
    region: Optional[str] = None,
    severity: Optional[str] = None
) -> List[dict]:
    """
    Generate a batch of phantom function logs for SIEM injection or analyst distraction.
    """
    return [_generate_phantom_event(f"{prefix}{random.randint(1000, 9999)}", region, severity) for _ in range(count)]


def write_phantom_logfile(
    out_path: str = "data/phantom_cloudtrail.json",
    count: int = 12,
    region: Optional[str] = None,
    prefix: str = "phantom-lambda-",
    severity: Optional[str] = None
):
    """
    Write CloudTrail-style logs to disk for injection or forensic poisoning.
    """
    batch = generate_phantom_log_batch(count, prefix, region, severity)
    logdoc = {
        "Records": batch
    }

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(logdoc, f, indent=2)
    logger.info(f"[PhantomTrail] Written {count} logs to {out_path}")


def inject_to_splunk(
    logs: List[dict],
    splunk_url: str,
    token: str,
    index: str = "main"
):
    """
    Inject phantom logs into Splunk HEC endpoint.
    """
    import requests

    headers = {
        "Authorization": f"Splunk {token}",
        "Content-Type": "application/json"
    }

    for event in logs:
        payload = {
            "event": event,
            "sourcetype": "aws:cloudtrail",
            "index": index,
            "time": time.time()
        }
        try:
            r = requests.post(splunk_url, headers=headers, data=json.dumps(payload), timeout=3)
            logger.info(f"[Splunk] Log injected: {r.status_code}")
        except Exception as e:
            logger.warning(f"[Splunk] Injection failed: {e}")


def inject_cloudtrail_phantoms(
    count: int = 10,
    output_path: Optional[str] = "data/phantom_cloudtrail.json",
    splunk_url: Optional[str] = None,
    splunk_token: Optional[str] = None,
    simulation: bool = False
):
    """
    Main CLI callable for phantom function injection campaign.
    """
    logs = generate_phantom_log_batch(count)

    if output_path:
        write_phantom_logfile(out_path=output_path, count=count)

    if splunk_url and splunk_token:
        if simulation:
            logger.info("[SIM] Would inject CloudTrail logs into Splunk")
        else:
            inject_to_splunk(logs, splunk_url, splunk_token)

    if simulation:
        for event in logs:
            logger.info(f"[SIM] Phantom event: {event['requestParameters']['functionName']} | {event['additionalEventData']['severityTag']}")
