import json
import datetime
import itertools
import collections.abc
import concurrent.futures

import boto3
import click
import colorama
import pandas as pd

import tabulate

from tchotcho.config import get_settings

colorama.init()


class SpotManager(object):
    def __init__(self):
        self.settings = get_settings()

    def _spot_history_wrapper(self, args):
        return self._spot_history(*args)

    def _spot_history(self, inst, region):
        client = boto3.client("ec2", region_name=region)
        prices = client.describe_spot_price_history(
            InstanceTypes=inst,
            ProductDescriptions=["Linux/UNIX", "Linux/UNIX (Amazon VPC)"],
            StartTime=(
                datetime.datetime.now() + datetime.timedelta(days=1)
            ).isoformat(),
            MaxResults=len(inst),
        )
        ret = prices["SpotPriceHistory"]
        return ret

    def list(self, gpu, region=None, inst=[], method="future-process"):
        if len(inst) == 0:
            with open(self.settings.GPU_INFO_FILE) as f:
                inst = json.load(f)["instance"]
                if gpu:
                    inst = [x["name"] for x in inst if x["gpu"] > 0 and x["supported"]]
                else:
                    inst = [x["name"] for x in inst]

        if not isinstance(inst, collections.abc.Sequence) or isinstance(inst, str):
            raise Exception("We need a list for inst!")

        client = boto3.client("ec2")
        regions = [
            (inst, x["RegionName"]) for x in client.describe_regions()["Regions"]
        ]

        if region:
            regions = [x for x in regions if region in x[1]]

        if method == "future-process":
            with concurrent.futures.ProcessPoolExecutor() as executor:
                results = list(executor.map(self._spot_history_wrapper, regions))
        else:
            results = [self._spot_history(*x) for x in regions]

        results = [x for x in results if x]

        results = list(itertools.chain.from_iterable(results))

        for x in results:
            x["SpotPrice"] = float(x["SpotPrice"])
        ret = sorted(results, key=lambda x: x["SpotPrice"])
        print(f"Found {len(results)} entries")
        return ret


mgr = SpotManager()


@click.group()
def spot():
    ...


@spot.command(name="list")
@click.option("--region", help="List spot prices in region")
@click.option(
    "--gpu/--no-gpu", default=True, help="Limit results to show only GPU instances"
)
@click.option("--inst", help="List spot prices for instance type", multiple=True)
@click.option("--csv/--no-csv", default=False)
def _list(gpu, region, inst, csv):
    ret = mgr.list(gpu, region, inst)

    def set_color(val):
        if val < 1:
            val = colorama.Back.GREEN + str(val) + colorama.Back.RESET
        elif val > 3:
            val = colorama.Back.RED + str(val) + colorama.Back.RESET
        else:
            val = colorama.Back.YELLOW + str(val) + colorama.Back.RESET
        return val

    # apply to specific column
    df = pd.DataFrame(ret)
    df = df[["InstanceType", "AvailabilityZone", "SpotPrice"]]
    to_print = df.to_csv()

    if not csv:
        df["SpotPrice"] = df["SpotPrice"].apply(set_color)
        to_print = tabulate.tabulate(
            df, headers="keys", tablefmt="fancy_grid", showindex="never"
        )
    print(to_print)
