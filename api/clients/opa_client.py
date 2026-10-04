from opa_client.opa import OpaClient
from fastapi import HTTPException


def get_opa_client():
    """
    Establish a connection with the OPA server.
    """
    opa_client = OpaClient()
    if opa_client.check_connection() != "Yes I'm here :)":
        raise HTTPException(
            status_code=404, detail="OPA server is not running"
        )
    return opa_client


def get_policies():
    """
    Fetch all available policies.
    """
    opa_client = get_opa_client()
    return opa_client.get_policies_list()


def get_opa_raw_data(name):
    """
    Fetch raw data from OPA server.
    """
    opa_client = get_opa_client()
    return opa_client.get_opa_raw_data(name)


def update_or_create_opa_data(data, name):
    """
    Update or create data in OPA server.    
    """
    opa_client = get_opa_client()
    opa_client.update_or_create_opa_data(data, name)
    return True


def check_policy(policy_name, rule_name, input_data):
    """
    Check a given policy with provided input data.
    """
    opa_client = get_opa_client()

    response = opa_client.check_permission(
        input_data=input_data, policy_name=policy_name, rule_name=rule_name
    )
    if 'result' in response:
        return response
    raise HTTPException(status_code=404, detail="Policy decision not found")


def create_opa_policy(policy_content, policy_name):
    """
    Create a new policy in OPA.
    """
    opa_client = get_opa_client()
    return opa_client.update_opa_policy_fromstring(policy_content, policy_name)


def update_policy(policy_status, policy_content):
    """
    Update an existing policy or create a new one if it doesn't exist.
    """
    opa_client = get_opa_client()
    return opa_client.update_opa_policy_fromstring(policy_content, policy_status)


def update_policies_file(name, path, force=False):
    """
    Update the policies file.
    """
    if force:
        delete_all_policies()
    client = get_opa_client()
    client.update_opa_policy_fromfile(path, endpoint=name)  # response is True
    policies = client.get_policies_list()
    if name in policies:
        return True
    raise HTTPException(
        status_code=404, detail="The policy was not saved in the OPA server. Please check the file and try again. Also, make sure the OPA server is running."
    )


def delete_opa_policy(policy_name):
    """
    Delete a policy from OPA.
    """
    opa_client = get_opa_client()
    return opa_client.delete_opa_policy(policy_name)


def delete_all_policies():
    """
    Delete all policies from OPA.
    """
    opa_client = get_opa_client()
    policies_list = opa_client.get_policies_list()
    for policy in policies_list:
        opa_client.delete_opa_policy(policy)
    return "All policies deleted successfully!"
