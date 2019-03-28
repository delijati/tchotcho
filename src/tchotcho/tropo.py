import boto3
import troposphere.iam
import troposphere.ec2
import troposphere
import troposphere.cloudformation
import textwrap
import awacs.aws
import awacs.sts
import awacs


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
    extra_user_data="",
):

    # TODO
    t = troposphere.Template()

    instance_security_group = t.add_resource(
        troposphere.ec2.SecurityGroup(
            "InstanceSecurityGroup",
            VpcId=get_default_vpc_id(),
            GroupDescription="Enable only SSH ingoing via port 22 and all outgoing",
            SecurityGroupIngress=[
                troposphere.ec2.SecurityGroupRule(
                    IpProtocol="tcp", FromPort="22", ToPort="22", CidrIp="0.0.0.0/0"
                ),
                troposphere.ec2.SecurityGroupRule(
                    IpProtocol="tcp", FromPort="22", ToPort="22", CidrIpv6="::/0"
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
                    troposphere.Sub(
                        textwrap.dedent(
                            """#!/bin/bash
                            set -x -e
                            apt-get update
                            apt-get install neovim -y

                            # extra user data
                            {extra_user_data}
                            """.format(
                                extra_user_data=extra_user_data
                            )
                        ),
                    )
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
            "Instance",
            LaunchTemplate=troposphere.ec2.LaunchTemplateSpecification(
                LaunchTemplateId=troposphere.Ref(launch_template),
                Version=troposphere.GetAtt(launch_template, "LatestVersionNumber"),
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

    return t.to_yaml()
