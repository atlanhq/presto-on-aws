<h1 align='center'>Presto on AWS</h1>


This is a cloudformation template for deploying [Presto](https://prestosql.io) on AWS. It deploys coordinators and workers in an autoscaling group.

## Features

- Graceful shutdown of workers using Autoscaling lifecycle management. Presto worker will not shutdown until all the queries finish on that worker.
- Highly available coordinator nodes. 
- Autoscaling of presto workers based on presto's memory and CPU usage. 
- A cloudwatch and prometheus agent which runs inside presto coordinator to push presto's metrics such as input data, CPU usage, running/blocked/failed queries. 
- A query logger which pushes completed queries and its stats to ElasticSearch. 
- A presto AMI creation packer script to easily update presto version. 
- Logs of presto coordinator and workers available in Cloudwatch.
- Health check in Presto workers to remove unhealthy workers

## Architecture

![Screen Shot 2020-06-04 at 8.52.37 PM](https://user-images.githubusercontent.com/10682054/83781909-c81ab280-a6ac-11ea-8e48-b36ec631f5ac.png)



## Pre-requisites

- A VPC and subnet
- A user with following permissions. // TODO: Add permissions

### Modiying the presto configuration

- New connectors: To add presto connectors (like hive connector, postgres connector etc) configuration to the deployment create a directory with following structure. Add properties file for each connector, zip the directory. Add the connector file copying command into the boostrap script in CFT. 
  ```
    ├── catalog 
    │   ├── hive.properties
    │   ├── jmx.properties
    │   ├── tpcds.properties
    │   └── tpch.properties
    └── config.properties
  ```

- To modify the core configuration such as enabling spill or reserved pool disabling/enabling modify the config.properties file mentioned above. Memory based configurations like JVM memory, max memory per node is automatically handled based on selected instances. 

Add the URL of above directory as zip file in `AdditionalConfigsUri` parameter in CFT. 

### Creating Presto AMI using Packer

 - Go inside `packer` directory and change the parameters of `.atlanrc` file. The presto version is 330 by default. Source AMI is Amazon Linux 2 in the region you want to create the AMI in. 
 - Run the following command
  ```bash
    make build_presto_image
  ```
 - Change the `presto.json` to modify the AMI further. 
 - To use this AMI add the AMI ID in the mapping in `presto.yaml` with AMI's region. 

### Deployment

The CFT requires following parameters for deployment
 - VPC ID: VPC to deploy Presto cluster
 - Subnet ID: Subnet to deploy Presto cluster
 - Security groups ID: SGs to attach to presto coordinators and workers
 - Keyname: Private key to use to launch presto machines
 - Coordinator Instance type: EC2 Instance type for coordinator
 - Coordinator Instance Count: For HA Coordinator deployment set it to 2 else set it to 1. 
 - Min workers count: Minimum numbers of EC2 machines in Presto workers ASG
 - Max workers count: Maximum numbers of EC2 machines in Presto workers ASG
 - Workers instance type: EC2 Instance type for workers
 - Presto Version: Presto version, required for compatibility before and after version 330
 - EC2 Root volume size: EBS Volume size (GB) for presto workers and coordinators. Increase the value to few hundred GBs if you have disk spill based workload. 
 - Hive IP: Format `thrift://<ip>:9083`
 - Elasticsearch Host: Elasticsearch host for query logger to push SQL queries into. 
 - Elasticsearch Port: Elasticsearch port for query logger to push SQL queries into
 - Environment: Identifier for Dev, Production presto clusters.
 
Create the AMI and provide the ID with region in CFT. Now deploy the CFT by following the guide from AWS.

### Configuring autoscaling of workers

You can configure presto workers autoscaling based on metrics from presto like running queries, heap usage etc. These metrics gets pushed into Cloudwatch by presto coordinator. You can configure the Cloudwatch alarams and autoscaling based on these Cloudwatch Metrics. 

### Limitations/Future work
 - Add support for TLS in the deployment. 
 - Graceful shutdown lambda only waits for 1 hour for queries to finish. Add feature to wait to terminate the worker until all the queries finish on that worker.
 - High availibility feature only switches between standby and live coordinator but doesn't restart the failed coordinator. 
 - No retention policy configuration for presto logs in Cloudwatch

### Contribute

1. Fork it
2. Create your feature branch (`git checkout -b my-new-feature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin my-new-feature`)
5. Create new Pull Request
