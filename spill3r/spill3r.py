#!/usr/bin/env python3
"""
Spill3r - S3 Bucket Misconfiguration Scanner
Scan public S3 buckets for list and write vulnerabilities.
"""

import argparse
import requests
import threading
import queue
import json
from datetime import datetime

try:
    from rich.console import Console

    console = Console()
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

BUCKET_CHECK_QUEUE = queue.Queue()
TEST_OBJECT_KEY = "spill3r-test-object.txt"
TEST_OBJECT_CONTENT = "This is a test file uploaded by Spill3r."
scan_results = []

REGIONS = [
    "us-east-1", "us-east-2", "us-west-1", "us-west-2",
    "af-south-1", "ap-east-1", "ap-south-1", "ap-south-2",
    "ap-northeast-1", "ap-northeast-2", "ap-northeast-3",
    "ap-southeast-1", "ap-southeast-2", "ap-southeast-3", "ap-southeast-4",
    "ca-central-1",
    "cn-north-1", "cn-northwest-1",
    "eu-central-1", "eu-central-2",
    "eu-north-1", "eu-south-1", "eu-south-2", "eu-west-1", "eu-west-2", "eu-west-3",
    "me-central-1", "me-south-1",
    "sa-east-1"
]


def get_s3_urls(bucket: str, region_only: str = None) -> list:
    if region_only:
        return [f"https://{bucket}.s3.{region_only}.amazonaws.com"]
    return [f"https://{bucket}.s3.amazonaws.com"] + [
        f"https://{bucket}.s3.{region}.amazonaws.com" for region in REGIONS
    ]


def check_bucket_listable(bucket: str, region_only: str = None) -> bool:
    for url in get_s3_urls(bucket, region_only):
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200 and "<ListBucketResult" in r.text:
                return True
        except requests.RequestException:
            continue
    return False


def check_bucket_writeable(bucket: str, cleanup: bool = False, dry_run: bool = False, region_only: str = None) -> bool:
    if dry_run:
        return True

    for base_url in get_s3_urls(bucket, region_only):
        object_url = f"{base_url}/{TEST_OBJECT_KEY}"
        headers = {"Content-Type": "text/plain"}
        try:
            put_response = requests.put(object_url, headers=headers, data=TEST_OBJECT_CONTENT, timeout=5)
            if put_response.status_code in [200, 201]:
                if cleanup:
                    try:
                        delete_response = requests.delete(object_url, timeout=5)
                        return delete_response.status_code in [204, 200]
                    except requests.RequestException:
                        pass
                return True
        except requests.RequestException:
            continue
    return False


def log_result(bucket: str, listable: bool, writeable: bool, dry_run: bool):
    scan_results.append({
        "bucket": bucket,
        "listable": listable,
        "writeable": writeable,
        "dry_run": dry_run,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })


def worker(write_check=False, cleanup=False, dry_run=False, region_only=None):
    while not BUCKET_CHECK_QUEUE.empty():
        bucket = BUCKET_CHECK_QUEUE.get()
        listable = check_bucket_listable(bucket, region_only)
        writeable = check_bucket_writeable(bucket, cleanup, dry_run, region_only) if write_check else False

        if RICH_AVAILABLE:
            console.print(f"[bold cyan]{bucket}[/] - "
                          f"{'[green]Listable[/]' if listable else '[red]Not listable[/]'}, "
                          f"{'[green]Writeable[/]' if writeable else '[red]Not writeable[/]'}"
                          f"{' [yellow](dry-run)[/]' if dry_run else ''}")
        else:
            print(f"{bucket}: "
                  f"{'Listable' if listable else 'Not listable'}, "
                  f"{'Writeable' if writeable else 'Not writeable'}"
                  f"{' (dry-run)' if dry_run else ''}")

        log_result(bucket, listable, writeable, dry_run)
        BUCKET_CHECK_QUEUE.task_done()


def scan_buckets(wordlist: str, threads: int, write_check=False, cleanup=False, dry_run=False, region_only=None):
    with open(wordlist, "r") as f:
        for line in f:
            bucket = line.strip()
            if bucket:
                BUCKET_CHECK_QUEUE.put(bucket)

    for _ in range(min(threads, BUCKET_CHECK_QUEUE.qsize())):
        t = threading.Thread(target=worker, args=(write_check, cleanup, dry_run, region_only))
        t.daemon = True
        t.start()

    BUCKET_CHECK_QUEUE.join()


def main():
    print(r"""
  _________        .__ .__   .__   ________           
 /   _____/______  |__||  |  |  |  \_____  \ _______  
 \_____  \ \____ \ |  ||  |  |  |    _(__  < \_  __ \ 
 /        \|  |_> >|  ||  |__|  |__ /       \ |  | \/ 
/_______  /|   __/ |__||____/|____//______  / |__|    
        \/ |__|                           \/         
                 By Raydar
        https://github.com/jarrad411
    """)

    parser = argparse.ArgumentParser(
        description="Spill3r: S3 Bucket Misconfiguration Scanner"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-b", "--bucket", help="Single bucket name to scan")
    group.add_argument("-w", "--wordlist", help="File containing list of buckets to scan")

    parser.add_argument("-t", "--threads", type=int, default=5, help="Number of threads to use")
    parser.add_argument("--write-check", action="store_true", help="Enable public write test")
    parser.add_argument("--cleanup", action="store_true", help="Delete test object after upload")
    parser.add_argument("--dry-run", action="store_true", help="Simulate write-check without uploading")
    parser.add_argument("--region-only", help="Only test this specific S3 region (e.g. us-east-2)")
    parser.add_argument("-o", "--output", help="Save results to a JSON file")

    args = parser.parse_args()

    if args.bucket:
        is_listable = check_bucket_listable(args.bucket, args.region_only)
        is_writeable = check_bucket_writeable(args.bucket, args.cleanup, args.dry_run,
                                              args.region_only) if args.write_check else False
        result = f"{args.bucket}: " \
                 f"{'Listable' if is_listable else 'Not listable'}, " \
                 f"{'Writeable' if is_writeable else 'Not writeable'}" \
                 f"{' (dry-run)' if args.dry_run else ''}"
        print(result)
        log_result(args.bucket, is_listable, is_writeable, args.dry_run)
    elif args.wordlist:
        scan_buckets(args.wordlist, args.threads, args.write_check, args.cleanup, args.dry_run, args.region_only)

    if args.output:
        try:
            with open(args.output, "w") as outfile:
                json.dump(scan_results, outfile, indent=2)
            if RICH_AVAILABLE:
                console.print(f"[bold green]Results saved to {args.output}[/]")
            else:
                print(f"Results saved to {args.output}")
        except Exception as e:
            print(f"Failed to save output: {e}")


if __name__ == "__main__":
    main()
