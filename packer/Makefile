FILE := .atlanrc
-include ./$(FILE)

build_presto_image:
	@packer build \
		-var 'vpc_id=$(VPC_ID)' \
		-var 'subnet_id=$(SUBNET_ID)' \
		-var 'aws_access_key=$(AWS_ACCESS_KEY)' \
		-var 'aws_secret_key=$(AWS_SECRET_KEY)' \
		-var 'presto_version=$(PRESTO_VERSION)' \
		-var 'ami_name=$(AMI_NAME)' \
		-var 'source_ami=$(SOURCE_AMI)' \
		-var 'region=$(REGION)' \
		presto.json

validate_config:
	@packer validate presto.json
