import boto3
import os
import troposphere.iam
import troposphere.ec2
import troposphere
import troposphere.cloudformation
import troposphere.policies
import textwrap
import awacs.aws
import awacs.sts
import awacs


USER_SCRIPT_DEFAULT = """#!/bin/bash
set -x -e
# See logs:
# /var/log/cloud-init.log and
# /var/log/cloud-init-output.log
# /var/log/user-data.log

exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

echo "BEGIN"
date '+%Y-%m-%d %H:%M:%S'

# remove ubuntu daily updates
# https://unix.stackexchange.com/a/480986
flock /var/lib/apt/daily_lock apt update
flock /var/lib/apt/daily_lock apt install neovim silversearcher-ag python-pip -y

# install tool to signal that we are ready
pip install https://s3.amazonaws.com/cloudformation-examples/aws-cfn-bootstrap-latest.tar.gz

echo "START # Extra user data #"

<<extra_user_data>>

echo "END # Extra user data #"

# Setup the ec2 train !!! only needed if we have metadata
# cfn-init -v --stack ${AWS::StackName} --resource TchoTchoInstance --region ${AWS::Region}

# Signal the status of cfn-init
cfn-signal -e $? --stack ${AWS::StackName} --resource TchoTchoInstance --region ${AWS::Region}

echo "END"
"""


def get_default_vpc_id():
    """Returns a default VPC id or None"""
    ec2 = boto3.client("ec2")
    res = ec2.describe_vpcs(Filters=[{"Name": "isDefault", "Values": ["true"]}])
    if not len(res["Vpcs"]):
        return None
    return res["Vpcs"][0]["VpcId"]


def create_cloudformation(
    key_name,
    ami_id,
    instance_type,
    security_group=None,
    subnet_id=None,
    price=None,
    size=100,
    user_script=USER_SCRIPT_DEFAULT,
    extra_user_data="",
):
    user_script = USER_SCRIPT_DEFAULT.replace("<<extra_user_data>>",
                                              extra_user_data)
    # XXX set this to get real bool values
    os.environ["TROPO_REAL_BOOL"] = "true"

    t = troposphere.Template(Description="TchoTcho EC2 train")

    instance_security_group = t.add_resource(
        troposphere.ec2.SecurityGroup(
            "InstanceSecurityGroup",
            VpcId=get_default_vpc_id(),
            GroupDescription="Enable only SSH ingoing via port 22 and all outgoing",
            SecurityGroupIngress=[
                troposphere.ec2.SecurityGroupRule(
                    IpProtocol="tcp", FromPort=22, ToPort=22, CidrIp="0.0.0.0/0"
                ),
                troposphere.ec2.SecurityGroupRule(
                    IpProtocol="tcp", FromPort=22, ToPort=22, CidrIpv6="::/0"
                ),
            ],
            SecurityGroupEgress=[
                troposphere.ec2.SecurityGroupRule(IpProtocol="-1", CidrIp="0.0.0.0/0"),
                troposphere.ec2.SecurityGroupRule(IpProtocol="-1", CidrIpv6="::/0"),
            ],
        )
    )

    instance_role = t.add_resource(
        troposphere.iam.Role(
            "InstanceRole",
            AssumeRolePolicyDocument=awacs.aws.Policy(
                Version="2012-10-17",
                Statement=[
                    awacs.aws.Statement(
                        Effect=awacs.aws.Allow,
                        Principal=awacs.aws.Principal("Service", "ec2.amazonaws.com"),
                        Action=[awacs.sts.AssumeRole],
                    ),
                ],
            ),
            ManagedPolicyArns=[
                "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role",
            ],
            Policies=[
                troposphere.iam.Policy(
                    PolicyName="S3FullAccess",
                    PolicyDocument={
                        "Statement": [
                            {"Effect": "Allow", "Action": "s3:*", "Resource": "*"}
                        ],
                    },
                )
            ],
        )
    )

    instance_profile = t.add_resource(
        troposphere.iam.InstanceProfile(
            "InstanceProfile", Roles=[troposphere.Ref(instance_role)],
        )
    )

    launch_template = t.add_resource(
        troposphere.ec2.LaunchTemplate(
            "InstanceLaunchTemplate",
            # https://github.com/cloudtools/troposphere/blob/07dde6b66fca28dd401903027d8ac13bc107e0b6/examples/CloudFormation_Init_ConfigSet.py#L45
            # https://stackoverflow.com/questions/35095950/what-are-the-benefits-of-cfn-init-over-userdata
            # XXX for now we are not using this we always just delete the stack
            # Metadata=troposphere.cloudformation.Metadata(
            #     troposphere.cloudformation.Init(
            #         troposphere.cloudformation.InitConfigSets(default=["bootstrap"]),
            #         awspackages=troposphere.cloudformation.InitConfig(
            #             commands={
            #                 "001-bootstrap": {"command": "touch ~/bootstra.txt"},
            #             },
            #         ),
            #     ),
            # ),
            LaunchTemplateData=troposphere.ec2.LaunchTemplateData(
                KeyName=key_name,
                ImageId=ami_id,
                InstanceType=instance_type,
                UserData=troposphere.Base64(
                    # Sub is needed if we have variables
                    troposphere.Sub(
                        textwrap.dedent(
                            user_script.strip()
                        ),
                    ),
                ),
                IamInstanceProfile=troposphere.ec2.IamInstanceProfile(
                    Arn=troposphere.GetAtt(instance_profile, "Arn"),
                ),
                BlockDeviceMappings=[
                    troposphere.ec2.LaunchTemplateBlockDeviceMapping(
                        DeviceName="/dev/sda1",
                        Ebs=troposphere.ec2.EBSBlockDevice(
                            DeleteOnTermination=True, VolumeSize=size, Encrypted=True
                        ),
                    )
                ],
            ),
        )
    )

    if price:
        instance_market_options = troposphere.ec2.InstanceMarketOptions(
            MarketType="spot",
            SpotOptions=troposphere.ec2.SpotOptions(
                SpotInstanceType="one-time",
                MaxPrice=str(price),
                InstanceInterruptionBehavior="terminate",
            ),
        )

        launch_template.properties["LaunchTemplateData"].properties[
            "InstanceMarketOptions"
        ] = instance_market_options

    if not security_group:
        security_group = [troposphere.Ref(instance_security_group)]

    if subnet_id:
        network_interfaces = [
            troposphere.ec2.NetworkInterfaces(
                SubnetId=subnet_id, DeviceIndex=0, Groups=[security_group],
            )
        ]

        launch_template.properties["LaunchTemplateData"].properties[
            "NetworkInterfaces"
        ] = network_interfaces
    else:
        launch_template.properties["LaunchTemplateData"].properties[
            "SecurityGroupIds"
        ] = [troposphere.Ref(instance_security_group)]

    ec2_instance = t.add_resource(
        troposphere.ec2.Instance(
            "TchoTchoInstance",
            LaunchTemplate=troposphere.ec2.LaunchTemplateSpecification(
                LaunchTemplateId=troposphere.Ref(launch_template),
                Version=troposphere.GetAtt(launch_template, "LatestVersionNumber"),
            ),
            CreationPolicy=troposphere.policies.CreationPolicy(
                ResourceSignal=troposphere.policies.ResourceSignal(Timeout='PT15M')
            ),
        )
    )

    t.add_output(
        [
            troposphere.Output(
                "InstanceId",
                Description="InstanceId of the EC2 instance",
                Value=troposphere.Ref(ec2_instance),
            ),
            troposphere.Output(
                "AZ",
                Description="Availability Zone of the EC2 instance",
                Value=troposphere.GetAtt(ec2_instance, "AvailabilityZone"),
            ),
            troposphere.Output(
                "PublicIP",
                Description="Public IP address of the EC2 instance",
                Value=troposphere.GetAtt(ec2_instance, "PublicIp"),
            ),
            troposphere.Output(
                "PrivateIP",
                Description="Private IP address of the EC2 instance",
                Value=troposphere.GetAtt(ec2_instance, "PrivateIp"),
            ),
            troposphere.Output(
                "PublicDNS",
                Description="Public DNSName of the EC2 instance",
                Value=troposphere.GetAtt(ec2_instance, "PublicDnsName"),
            ),
            troposphere.Output(
                "PrivateDNS",
                Description="Private DNSName of the EC2 instance",
                Value=troposphere.GetAtt(ec2_instance, "PrivateDnsName"),
            ),
        ]
    )
    # XXX moto has some problems with yaml; validate, LaunchTemplateData is
    # not parsed so the ec2instance ImageId other keys are not found
    # return t.to_yaml()
    return t.to_json()
