import boto3
import json

def make_sts_connection(id):
    sts_connection = boto3.client('sts')
    
    role_arn = "arn:aws:iam::{}:role/Target-Role-EC2-Access".format(id)
    role_session_name = "cross_acct_lambda"
    target_account = sts_connection.assume_role(RoleArn = role_arn , RoleSessionName = role_session_name)   
    
    ACCESS_KEY = target_account['Credentials']['AccessKeyId']
    SECRET_KEY = target_account['Credentials']['SecretAccessKey']
    SESSION_TOKEN = target_account['Credentials']['SessionToken']
    
    return ACCESS_KEY , SECRET_KEY , SESSION_TOKEN

def lambda_handler(event, context):
   
    org_connection = boto3.client('organizations')
    
    response = org_connection.list_accounts()
    
    accounts = response["Accounts"]
    
    final_count = 0
    org_dict = {}
    
    print()             # print empty line
    
    for account in accounts:
        ACCESS_KEY , SECRET_KEY , SESSION_TOKEN = make_sts_connection(account["Id"])
        #print(ACCESS_KEY, SECRET_KEY, SESSION_TOKEN)
        
        current_session = boto3.session.Session(aws_access_key_id=ACCESS_KEY,aws_secret_access_key=SECRET_KEY,aws_session_token=SESSION_TOKEN)
        
        ec2_client = current_session.client('ec2')
        
        ec2_regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]
        total_count = 0
        account_list = []
        
        for region in ec2_regions:
            count = 0
            region_list = []
            ec2_resource = current_session.resource('ec2',region_name=region)
            instances = ec2_resource.instances.filter()
            
            for instance in instances:
                instance_list = []
                if instance.state["Name"] == "running":
                    count = count + 1
                    instance_list.append(instance.id)
                   #print(instance.id)
                    instance_list.append(instance.instance_type)
                    instance_list.append(instance.public_ip_address)
                    instance_list.append(region)
                    #print(region)
                    #print("--")
                    region_list.append(instance_list)
                    #print (instance.id, instance.instance_type, region)
            if(count != 0):
                print("Number of Instances running in Region {} for AWS Account ID {} : {}".format(region.upper(),account["Id"],count))
                total_count = total_count + count
                account_list.append(region_list)
        
        print("Number of Instances running in the AWS Account {} : {}".format(account["Id"],total_count))
        print("---------------------------------------------------")
        final_count = final_count + total_count
        org_dict[account["Id"]] = account_list
    
    print("\nTotal Number of Instances running in the whole AWS Organization : {} \n".format(final_count))
    
    #print(org_dict)
    
'''    
    json_object = json.dumps(org_dict, indent = 4)
    print(json_object)
    
    with open("sample.json", "w") as outfile:
        json.dump(dictionary, outfile)
        
'''        