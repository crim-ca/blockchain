import argparse
import requests
import statistics
import time


def run_test(url, method="GET", body=None, json=None, runs=100, replica=1):
    reps = []
    for rep in range(replica):
        times = []
        responses = []
        for i in range(runs):
            t = time.perf_counter()
            r = requests.request(method, url, data=body, json=json)
            times.append((time.perf_counter() - t) * 1000)

        assert all(r in [200, 201] for r in responses), "Invalid responses, cannot test times"
        reps.append({"avg": statistics.mean(times), "stddev": statistics.stdev(times),
                     "total": sum(times), "times": times})
        print("== Replica", rep)
        print("   Results for", runs, "test runs")
        print("   Average Delta Time (ms):", reps[-1]["avg"])
        print("   Std Dev Delta Time (ms):", reps[-1]["stddev"])
        print("   Total Delta Time (ms):", reps[-1]["total"])

    print("Min Avg Delta (ms):", min([rep["avg"] for rep in reps]))
    print("Max Avg Delta (ms):", max([rep["avg"] for rep in reps]))
    print("All Avg Delta (ms):", statistics.mean([rep["avg"] for rep in reps]))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-r", "--runs", type=int, default=100, help="Number of test runs (default: %(default)s)")
    ap.add_argument("-R", "--replica", type=int, default=1, help="Replicated test runs (default: %(default)s)")
    ap.add_argument("-u", "--url", type=str, required=True, help="Request endpoint.")
    ap.add_argument("-m", "--method", type=str, default="GET", help="Request method (default: %(default)s).")
    ap_body = ap.add_mutually_exclusive_group()
    ap_body.add_argument("-b", "--body", type=str, help="Request body (RAW)")
    ap_body.add_argument("-j", "--json", type=str, help="Request body (JSON)")
    ns = ap.parse_args()
    run_test(**vars(ns))
