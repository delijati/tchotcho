[![pipeline status](https://gitlab.com/delijati/tchotcho/badges/master/pipeline.svg)](https://gitlab.com/delijati/tchotcho/commits/master)
[![coverage report](https://gitlab.com/delijati/tchotcho/badges/master/coverage.svg)](https://gitlab.com/delijati/tchotcho/commits/master)

# TchoTcho

```
 (tchotcho)OOOOOoo...
         _____      oo
 _______ ||_||__n_n__I_
 |__T__|-|_T_|_________)>
  oo oo   o ()() ()() o\
```

Train on EC2 when you are ready with experimenting!

This tool contains bundle of methods to setup a EC2 instance for training.

## Install

```
❯ pip install tchotcho
```

### Requirements

- Setup a private/ public key (login to EC2, helpful for cloning private repo)
- Install rsync (copy project to EC2)
- Install ssh (execute commands remote on EC2)
- Setup your aws credentials profile via (`~/.aws/credentials`)

## Actions

Available commands:

```
❯ tchotcho --help
Usage: tchotcho [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  info
  key
  shell
  spot
  stack
```

## Info

### Update

Retrieves list of EC2 instances from https://ec2instances.info/ and queries aws
to find suitable ami imges for training. It caches the result locally for later
usage.

Help:

```
❯ AWS_PROFILE=dev tchotcho info update --help
Usage: tchotcho info update [OPTIONS]

  Update the GPU info json file

Options:
  --ownerid TEXT     Owner id used (we use ubuntu)  [default: 898082745236;
                     required]

  --namefilter TEXT  AMI filter by name  [default: Deep Learning AMI* 18.04*;
                     required]

  --limit INTEGER    Number of AMI image  [default: 5; required]
  --csv / --no-csv
  --region TEXT      List in region  [required]
  --help             Show this message and exit.
```

Usage:

```
❯ AWS_PROFILE=dev env/bin/tchotcho info update
╒═══════════════╤═══════╤══════════════╤═══════════════════════╤═══════╤═══════════╤═════════════╤═══════════════╕
│ name          │   gpu │   gpu_memory │ gpu_model             │   cpu │    memory │ supported   │ price         │
╞═══════════════╪═══════╪══════════════╪═══════════════════════╪═══════╪═══════════╪═════════════╪═══════════════╡
│ p2.16xlarge   │    16 │          192 │ NVIDIA Tesla K80      │    64 │   732     │ True        │ 21.216        │
├───────────────┼───────┼──────────────┼───────────────────────┼───────┼───────────┼─────────────┼───────────────┤
│ p3dn.24xlarge │     8 │          256 │ NVIDIA Tesla V100     │    96 │   768     │ True        │ Not available │
├───────────────┼───────┼──────────────┼───────────────────────┼───────┼───────────┼─────────────┼───────────────┤
│ p2.8xlarge    │     8 │           96 │ NVIDIA Tesla K80      │    32 │   488     │ True        │ 10.608        │
...
╒══════════════╤═══════════════════════════════════════════════╤══════════════════════════╤═══════════════════════╕
│ region       │ name                                          │ date                     │ ami                   │
╞══════════════╪═══════════════════════════════════════════════╪══════════════════════════╪═══════════════════════╡
│ eu-central-1 │ Deep Learning AMI (Ubuntu 18.04) Version 29.0 │ 2020-05-20T14:57:39.000Z │ ami-062a3145bcf312c71 │
├──────────────┼───────────────────────────────────────────────┼──────────────────────────┼───────────────────────┤
│ eu-central-1 │ Deep Learning AMI (Ubuntu 18.04) Version 28.1 │ 2020-05-03T19:46:44.000Z │ ami-061aaaac62de85935 │
├──────────────┼───────────────────────────────────────────────┼──────────────────────────┼───────────────────────┤
│ eu-central-1 │ Deep Learning AMI (Ubuntu 18.04) Version 28.0 │ 2020-04-29T09:32:42.000Z │ ami-0f162c7e9b0e7d6f1 │
├──────────────┼───────────────────────────────────────────────┼──────────────────────────┼───────────────────────┤
│ eu-central-1 │ Deep Learning AMI (Ubuntu 18.04) Version 27.0 │ 2020-03-03T03:13:27.000Z │ ami-09633db638556dc39 │
├──────────────┼───────────────────────────────────────────────┼──────────────────────────┼───────────────────────┤
│ eu-central-1 │ Deep Learning AMI (Ubuntu 18.04) Version 26.0 │ 2019-12-02T22:09:33.000Z │ ami-0dcdcc4bc9e75005f │
╘══════════════╧═══════════════════════════════════════════════╧══════════════════════════╧═══════════════════════╛
```

### List

Use the cached result from `update` command from `~/.tchotcho/gpu_info.json`.

## Key

Function to manage keys on EC2.

```
❯ AWS_PROFILE=dev tchotcho key --help
Usage: tchotcho key [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  create
  delete
  fingerprint
  import
  list
```

## Shell

Currently rsync and ssh are implemented.

### Rsync

Sync your local experiment to EC2. The folder `.git` is excluded and all rules
are applied from `.gitignore`.

Usage:

```
❯ tchotcho shell rsync --src . --dst ubuntu@1.2.3.4:/home/ubuntu/project --privat-key ~/.ssh/id_rsa
```

### Ssh

Execute remote command on EC2.

Usage:

```
❯ tchotcho shell ssh --host ubuntu@1.2.3.4 --privat-key ~/.ssh/id_rsa --cmd "pwd && date"
```

## Spot

List spot price for given instances and regions.

```
❯ AWS_PROFILE=dev tchotcho spot list --help
Usage: tchotcho spot list [OPTIONS]

Options:
  --region TEXT     List spot prices in region
  --gpu / --no-gpu  Limit results to show only GPU instances
  --inst TEXT       List spot prices for instance type
  --csv / --no-csv
  --help            Show this message and exit.
```

### List

List spot price by default only supported GPU instances are shown.

Usage:

```
❯ AWS_PROFILE=dev tchotcho spot list --region eu-central-1
╒════════════════╤════════════════════╤═════════════╕
│ InstanceType   │ AvailabilityZone   │   SpotPrice │
╞════════════════╪════════════════════╪═════════════╡
│ g4dn.xlarge    │ eu-central-1b      │      0.1974 │
├────────────────┼────────────────────┼─────────────┤
│ g4dn.xlarge    │ eu-central-1a      │      0.1974 │
├────────────────┼────────────────────┼─────────────┤
│ g3.4xlarge     │ eu-central-1b      │      0.4275 │
├────────────────┼────────────────────┼─────────────┤
│ g3.4xlarge     │ eu-central-1a      │      0.4275 │
...
│ g3.16xlarge    │ eu-central-1a      │      1.71   │
├────────────────┼────────────────────┼─────────────┤
│ g4dn.16xlarge  │ eu-central-1b      │      1.8593 │
├────────────────┼────────────────────┼─────────────┤
│ p3.8xlarge     │ eu-central-1b      │      4.5876 │
├────────────────┼────────────────────┼─────────────┤
│ p3.8xlarge     │ eu-central-1a      │      4.5876 │
├────────────────┼────────────────────┼─────────────┤
│ p3.16xlarge    │ eu-central-1b      │      9.1752 │
├────────────────┼────────────────────┼─────────────┤
│ p2.8xlarge     │ eu-central-1b      │     10.608  │
├────────────────┼────────────────────┼─────────────┤
│ p2.8xlarge     │ eu-central-1a      │     10.608  │
╘════════════════╧════════════════════╧═════════════╛
```

## Stack

Core of this tool create a EC2 instance via cloudformation.

```
❯ AWS_PROFILE=dev tchotcho stack --help
Usage: tchotcho stack [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  create
  delete
  list
```

## Create

Create a cloudformation stack. The name needs to be the same as the imported
key in aws.

Usage:

```
❯ AWS_PROFILE=dev tchotcho stack create --help
Usage: tchotcho stack create [OPTIONS]

Options:
  --name TEXT            Name of stack to create && key  [required]
  --ami TEXT             Name of ami to use  [default: ami-061aaaac62de85935;
                         required]

  --inst TEXT            Name of the instance to use  [required]
  --security_group TEXT  Name of the security group to use
  --subnet TEXT          Name of the subnet to use
  --price FLOAT          Name of the instance to use
  --size INTEGER         Size of the disk in GB
  --dry / --no-dry       Only print yaml no create
  --help                 Show this message and exit.
```

Example:

```
❯ AWS_PROFILE=dev tchotcho stack create --name test-dl --inst t2.medium --price 0.02 --dry
```

### User script

TODO Currently only via the api changeable. Explain:

- waiting for apt via flock
- signal to cloudformation so we wait until user script install is finished

## Code style

We use `flake8` to ensure code quality and `black` to autoformat code.

Add it as a git-hook:

```
$ flake8 --install-hook git
$ git config --bool flake8.strict true
```

## TODO

- Try paramiko + scp to be pure python
