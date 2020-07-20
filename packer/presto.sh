#! /bin/bash
set -euxo
echo "HELLO WORLD"

version=$presto_version

echo $version
# Install Java
sudo amazon-linux-extras install java-openjdk11
java -version
sudo yum install -y awslogs aws-cfn-bootstrap

sudo mkdir -p /usr/lib/presto /var/log/presto /var/lib/presto/data /var/lib/presto/spill /etc/presto_metrics /etc/presto_scaling_service /var/run/presto

# Install presto
wget -O /tmp/presto-server.tar.gz https://repo1.maven.org/maven2/io/prestosql/presto-server/$version/presto-server-$version.tar.gz
tar -xvf /tmp/presto-server.tar.gz -C /tmp/
sudo cp -r /tmp/presto-server-$version/* /usr/lib/presto/
ls /usr/lib/presto


sudo chown -R ec2-user:ec2-user /etc/presto /usr/lib/presto /var/lib/presto /var/log/presto /etc/presto_metrics /etc/presto_scaling_service /var/run/presto

# install presto cli
wget -O /tmp/presto-cli https://repo1.maven.org/maven2/io/prestosql/presto-cli/$version/presto-cli-$version-executable.jar
sudo mv /tmp/presto-cli /usr/local/bin/presto-cli
sudo chmod +x /usr/local/bin/presto-cli

# create additional services

# presto metrics prometheus service

sudo wget -O /usr/local/bin/presto_metrics https://github.com/atlanhq/presto-metrics/releases/download/v1.0.0/presto_metrics_v1.0.0_linux_amd64
sudo chmod +x /usr/local/bin/presto_metrics
sudo chown -R ec2-user:ec2-user /usr/local/bin/presto_metrics


cat <<EOF > /etc/presto_metrics/env.prometheus
PRESTO_HOST=localhost
PRESTO_PORT=8080
SERVICE_NAME=prometheus
STACK_NAME=atlan-presto-test-stack
CLOUDWATCH_NAMESPACE=presto
EOF

cat <<EOF > /etc/presto_metrics/env.cloudwatch
PRESTO_HOST=localhost
PRESTO_PORT=8080
SERVICE_NAME=cloudwatch
STACK_NAME=atlan-presto-test-stack
CLOUDWATCH_NAMESPACE=presto
EOF

sudo touch /etc/default/presto && sudo chown ec2-user:ec2-user /etc/default/presto
/usr/bin/printf "PRESTO_OPTS= \
--pid-file=/var/run/presto/presto.pid \
--node-config=/etc/presto/node.properties \
--jvm-config=/etc/presto/jvm.config \
--config=/etc/presto/config.properties \
--launcher-log-file=/var/log/presto/launcher.log \
--server-log-file=/var/log/presto/server.log \
-Dhttp-server.log.path=/var/log/presto/http-request.log \
-Dcatalog.config-dir=/etc/presto/catalog
[Install]
WantedBy=default.target
" >> /etc/default/presto

sudo touch /etc/systemd/system/presto.service && sudo chown ec2-user:ec2-user /etc/systemd/system/presto.service

/usr/bin/printf "
[Unit]
Description=Presto Server
Documentation=https://prestosql.io/
After=network-online.target
[Service]
User=ec2-user
Restart=on-failure
Type=forking
PIDFile=/var/run/presto/presto.pid
RuntimeDirectory=presto
EnvironmentFile=/etc/default/presto
ExecStart=/usr/lib/presto/bin/launcher start \$PRESTO_OPTS
ExecStop=/usr/lib/presto/bin/launcher stop \$PRESTO_OPTS
[Install]
WantedBy=default.target
" >> /etc/systemd/system/presto.service


sudo cp /tmp/presto_metrics_prometheus.service /etc/systemd/system/presto_metrics_prometheus.service 
sudo cp /tmp/presto_metrics_cloudwatch.service /etc/systemd/system/presto_metrics_cloudwatch.service 

sudo systemctl daemon-reload
