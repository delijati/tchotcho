import json
import itertools
import concurrent.futures
import pandas as pd

import boto3
import click
import colorama
import requests

import tabulate

from tchotcho.config import get_settings

colorama.init()


class InfoManager(object):
    def __init__(self):
        self.settings = get_settings()

    def _get_ami(self, region, ownerid, namefilter, limit):
        rname = region["RegionName"]
        # print("Running query in region: %s" % rname)
        ec2 = boto3.client("ec2", region_name=rname)
        resp = ec2.describe_images(
            Owners=[ownerid], Filters=[{"Name": "name", "Values": [namefilter]}],
        )
        ret = []
        for image in resp["Images"]:
            ret.append((rname, image["Name"], image["CreationDate"], image["ImageId"]))
        # XXX return the newest <limit>
        ret = sorted(ret, key=lambda x: int(x[2].replace("-", "")[:8]), reverse=True)[
            :limit
        ]
        ret = [
            {"region": x[0], "name": x[1], "date": x[2], "ami": x[3]} for x in ret if x
        ]
        return ret

    def _get_ami_wrapper(self, args):
        return self._get_ami(*args)

    def get_ami_image(self, ownerid, namefilter, limit, method="future-process"):
        ec2 = boto3.client("ec2")
        response = ec2.describe_regions()
        regions = [(x, ownerid, namefilter, limit) for x in response["Regions"]]

        if method == "future-process":
            with concurrent.futures.ProcessPoolExecutor() as executor:
                data = list(executor.map(self._get_ami_wrapper, regions))
        else:
            data = [self._get_ami(*x) for x in regions]

        ret = list(itertools.chain.from_iterable(data))
        return ret

    def get_gpu_info(self):
        """
        Fetch gpu info from ec2instances.info
        """
        res = requests.get(
            "https://raw.githubusercontent.com/powdahound/ec2instances.info/master/www/instances.json"  # noqa
        )

        ret = []
        inst = res.json()

        for i in inst:
            # XXX has a gpu and g2 are old not supported gpu cards
            supported = i["GPU"] > 0 and not i["instance_type"].startswith("g2.")
            tmp = {
                "name": i["instance_type"],
                "gpu": i["GPU"],
                "cpu": i["vCPU"],
                "gpu_count": i.get("gpu_count"),
                "memory": i["memory"],
                "gpu_memory": i["GPU_memory"],
                "gpu_model": i["GPU_model"],
                "compute_capability": i.get("compute_capability"),
                "cuda_cores": i.get("cuda_cores"),
                "storage": i["storage"],
                "supported": supported,
            }

            pricing = {}
            for k in i["pricing"]:
                price = i["pricing"][k].get("linux", {}).get("ondemand")
                pricing[k] = float(price) if price else None
            tmp["pricing"] = pricing
            ret.append(tmp)
        return ret

    def update(self, ownerid, namefilter, limit):
        full = {}
        gpu_data = self.get_gpu_info()
        ami_data = self.get_ami_image(ownerid, namefilter, limit)
        full["instance"] = gpu_data
        full["ami"] = ami_data

        with open(self.settings.GPU_INFO_FILE, "w") as f:
            json.dump(full, f, indent=4)
        return full

    def list(self):
        with open(self.settings.GPU_INFO_FILE, "r") as f:
            return json.load(f)

    def render(self, data, region, csv):
        ami = data["ami"]
        gp = data["instance"]

        df = pd.DataFrame(gp)
        df_ami = pd.DataFrame(ami)
        df_ami = df_ami[df_ami.region == region]

        def set_price(val):
            val = val.get(region)
            val = float(val) if val else val
            return val

        df["price"] = df["pricing"].apply(set_price)

        def set_color(val):
            if str(val) != "nan":
                if val < 1:
                    val = colorama.Back.GREEN + str(val) + colorama.Back.RESET
                elif val > 3:
                    val = colorama.Back.RED + str(val) + colorama.Back.RESET
                else:
                    val = colorama.Back.YELLOW + str(val) + colorama.Back.RESET
            else:
                val = "Not available"
            return val

        def set_color_support(val):
            if val:
                val = colorama.Back.GREEN + str(val) + colorama.Back.RESET
            else:
                val = colorama.Back.YELLOW + str(val) + colorama.Back.RESET
            return val

        # apply to specific column
        df = df[
            [
                "name",
                "gpu",
                "gpu_count",
                "gpu_memory",
                "gpu_model",
                "compute_capability",
                "cuda_cores",
                "cpu",
                "memory",
                "supported",
                "price",
            ]
        ]
        df = df.sort_values(by=["gpu"], ascending=False)
        to_print = df.to_csv()
        if not csv:
            df["price"] = df["price"].apply(set_color)
            df["supported"] = df["supported"].apply(set_color_support)
            to_print = tabulate.tabulate(
                df, headers="keys", tablefmt="fancy_grid", showindex="never"
            )
        print(to_print)

        # ami
        to_print = df_ami.to_csv()
        if not csv:
            to_print = tabulate.tabulate(
                df_ami, headers="keys", tablefmt="fancy_grid", showindex="never"
            )
        print(to_print)


mgr = None


@click.group()
def info():
    global mgr
    mgr = InfoManager()


@info.command()
@click.option(
    "--ownerid",
    default="898082745236",
    required=True,
    help="Owner id used (we use ubuntu)",
    show_default=True,
)
@click.option(
    "--namefilter",
    default="Deep Learning AMI* 18.04*",
    show_default=True,
    help="AMI filter by name",
    required=True,
)
@click.option(
    "--limit",
    default=5,
    type=int,
    show_default=True,
    required=True,
    help="Number of AMI image",
)
@click.option("--csv/--no-csv", default=False)
@click.option("--region", help="List in region", required=True, default="eu-central-1")
def update(ownerid, namefilter, limit, csv, region):
    """Update the GPU info json file"""
    ret = mgr.update(ownerid, namefilter, limit)
    mgr.render(ret, region, csv)


@info.command(name="list")
@click.option("--region", help="List spot prices in region", required=True)
@click.option("--csv/--no-csv", default=False)
def _list(region, csv):
    """Get the GPU info"""
    ret = mgr.list()
    mgr.render(ret, region, csv)
