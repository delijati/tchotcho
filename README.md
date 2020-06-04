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

ec2 train instance setup

Find images:

aws ec2 describe-images --query 'reverse(sort_by(Images[*].{Id:ImageId,Type:VirtualizationType,Created:CreationDate,Storage:RootDeviceType, Desc:Name}, &Created))' --filters "Name=name,Values=Deep Learning AMI* 18.04*" --output table --region eu-central-1 --profile private

Detail info:

AWS_PROFILE=private aws ec2 describe-images --image-id ami-061aaaac62de85935

Flow:

- List avaidable gpu instances
- List avaidable ami images
- List spot prices for instance
- Create key pair if needed
- Start ami image with instance
  - Use spot bid or normal costs
  - Use script to initialize machine (remove stuff or install stuff)
  - Attach roles to image to be able to download files
- Execute ssh to machine or start via remote entrypoint ? paramiko ?

AWS_PROFILE=private aws cloudformation validate-template --template-body file://temp.yaml
AWS_PROFILE=private aws cloudformation create-stack --capabilities CAPABILITY_IAM --stack-name test-dl --template-body file://temp.yaml
AWS_PROFILE=private aws cloudformation list-stacks
AWS_PROFILE=private aws cloudformation describe-stacks --stack-name test-dl
AWS_PROFILE=private aws cloudformation describe-stack-events --stack-name test-dl
AWS_PROFILE=private aws cloudformation delete-stack --stack-name test-dl
sudo apt install s3fs
env/bin/pip install awscli


# rsync only repo files:
https://stackoverflow.com/questions/13713101/rsync-exclude-according-to-gitignore-hgignore-svnignore-like-filter-c
reset && rsync -ahvzn --delete --exclude .git --exclude-from=.git/ignores.tmp . ../foo 
rsync -anzP --delete --exclude .git --filter=":- .gitignore" . ../foo

## TODO

- Try paramiko + scp to be pure python
