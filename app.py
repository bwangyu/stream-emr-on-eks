# // Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# // SPDX-License-Identifier: License :: OSI Approved :: MIT No Attribution License (MIT-0)
#!/usr/bin/env python3
from aws_cdk import (App,Tags,CfnOutput,Aws)
from source.lib.emr_on_ec2_stack import EMREC2Stack
from source.lib.sm_notebook_stack import NotebookStack
from source.lib.lake_formation_stack import LFStack
from source.lib.msk_stack import MSKStack
from source.lib.spark_on_eks_stack import SparkOnEksStack
from source.lib.airflow_stack import AirflowStack

app = App()
proj_name = app.node.try_get_context('project_name')
emr_release_v=app.node.try_get_context('emr_version')

# 1.main stacks
eks_stack = SparkOnEksStack(app, proj_name, proj_name)
# 2.setup Lakeformation
lf_stack = LFStack(eks_stack, 'lake_formation',eks_stack.LFEngineerRole,eks_stack.datalake_bucket)
# 3.setup EMR on EC2
emr_ec2_stack = EMREC2Stack(eks_stack, 'emr-on-ec2', emr_release_v, proj_name, eks_stack.eksvpc, eks_stack.code_bucket, eks_stack.LFEngineerRole, eks_stack.LFAnalystRole,eks_stack.datalake_bucket.bucket_name)
# 4. the rest of nested stacks
msk_stack = MSKStack(eks_stack,'kafka', proj_name, eks_stack.eksvpc)
sagemaker_nb_stack = NotebookStack(eks_stack, 'sm_notebook', emr_ec2_stack.livy_sg, eks_stack.eksvpc, eks_stack.LFSagemakerRole, eks_stack.code_bucket)
airflow_stack = AirflowStack(eks_stack, "AirflowStack", eks_stack.eksvpc, "emr-serverless-airflow")

Tags.of(eks_stack).add('project', proj_name)
Tags.of(msk_stack).add('project', proj_name)
Tags.of(emr_ec2_stack).add('for-use-with-amazon-emr-managed-policies', 'true')
Tags.of(airflow_stack).add('project', proj_name)
Tags.of(sagemaker_nb_stack).add('project',proj_name)
Tags.of(lf_stack).add('project',proj_name)
# Deployment Output
CfnOutput(eks_stack,'CODE_BUCKET', value=eks_stack.code_bucket)
CfnOutput(eks_stack,"MSK_CLIENT_URL",
    value=f"https://{Aws.REGION}.console.aws.amazon.com/cloud9/ide/{msk_stack.Cloud9URL}",
    description="Cloud9 Url, Use this URL to access your command line environment in a browser"
)

CfnOutput(eks_stack, "MSK_BROKER", value=msk_stack.MSKBroker)
CfnOutput(eks_stack, "VirtualClusterId",value=eks_stack.EMRVC)
CfnOutput(eks_stack, "EMRExecRoleARN", value=eks_stack.EMRExecRole)
CfnOutput(airflow_stack, "MWAA_S3_BUCKET", value=airflow_stack.mwaa_s3bucket)
CfnOutput(airflow_stack, "MWAA_NAME", value=airflow_stack.mwaa_name)

app.synth()