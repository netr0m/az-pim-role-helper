import os
import sys
from enum import Enum
from typing import Dict, List, Optional, Tuple
from requests import HTTPError, post, Request, Session
from azure.identity import InteractiveBrowserCredential
import click

from models import *
from const import (
    AZ_RBAC_PIM_BASE_URL,
    AZ_RBAC_PIM_BASE_PATH,
    AZ_AUTHORITY,
    AZ_PIM_SCOPE
)

TENANT_ID = os.getenv("TENANT_ID")


def get_pim_access_token(tenant_id: str) -> Tuple[str, Dict[str, str]]:
    """
    Retrieve an access token for Azure PIM through interactive authentication

    Returns an access token and details about the signed-in user
    """
    try:
        print("Opening browser for Interactive Authentication...")
        credentials = InteractiveBrowserCredential(tenant_id=tenant_id, authority=AZ_AUTHORITY)
        token = credentials.get_token(AZ_PIM_SCOPE).token
        subject = {"id": credentials._auth_record.home_account_id.split(".")[0], "email": credentials._auth_record.username}
        print(f"Authenticated as {subject.get('email')}")
        return token, subject
    except Exception as e:
        print(e)
        sys.exit(1)


def pim_request(request: PIMRequest):
    """
    API client wrapper for Azure RBAC PIM
    """
    session = Session()
    try:
        url = f"{AZ_RBAC_PIM_BASE_URL}/{AZ_RBAC_PIM_BASE_PATH}/{request.resource_type}/{request.path}"
        headers = request.headers
        headers["Authorization"] = f"Bearer {request.token}"

        _req = Request(
            url=url,
            method=request.method,
            data=request.data,
            headers=headers,
            params=request.params,
            json=request.payload,
        )
        req = _req.prepare()
        response = session.send(req)
        response.raise_for_status()
        return response.json()
    except HTTPError as http_err:
        print(f"Response with status code {http_err.response.status_code} received:")
        if http_err.response.headers["Content-Type"] == "application/json":
            print(http_err.response.json())
        else:
            print(http_err.response.text)
        sys.exit(1)


def get_role_assignments(subject_id: str, resource_type: str = ResourceType.AZURE_RESOURCES, token: str = None) -> List[RoleAssignment]:
    """
    Retrieve a list of eligible role assignments for the signed-in user
    """
    print("Fetching Eligible Role Assignments from Azure PIM...")
    path = "roleAssignments"
    params = {
        "$expand": "linkedEligibleRoleAssignment,subject,scopedResource,roleDefinition($expand=resource)",
        "$filter": f"(subject/id eq '{subject_id}') and (assignmentState eq 'Eligible')",
        "$count": "true"
    }
    response = pim_request(PIMRequest(
        resource_type=resource_type,
        path=path,
        params=params,
        token=token
    ))

    role_assignments_response = RoleAssignmentsResponse(**response)

    return role_assignments_response.value


def request_role_assignment(
    subject_id: str, subscription_id: str,
    role_definition_id: str, role_assignment_id: str,
    resource_type: str = ResourceType.AZURE_RESOURCES,
    token: str = None
):
    """
    Request the activation of the given role assignment
    """
    print("Requesting activation of Role Assignment...")
    path = "roleAssignmentRequests"
    payload: RoleAssignmentRequest = RoleAssignmentRequest(
        roleDefinitionId=role_definition_id,
        resourceId=subscription_id,
        subjectId=subject_id,
        linkedEligibleRoleAssignmentId=role_assignment_id,
    )
    response = pim_request(PIMRequest(
        resource_type=resource_type,
        path=path,
        payload=payload,
        token=token
    ))

    role_assignment_request_response = RoleAssignmentRequestResponse(**response)

    return role_assignment_request_response


def get_role_assignment_by_subscription(
    role_assignments: List[RoleAssignment],
    subscription_name: Optional[str] = None,
    subscription_number: Optional[str] = None,
    role_type: Optional[RoleType] = None
) -> RoleAssignment:
    """
    Filter the eligible role assignments by subscription name, number (prefix) and/or role type
    """
    try:
        matches = []
        for role_assignment in role_assignments:
            role_resource_name = role_assignment.roleDefinition.resource.displayName.lower()
            if subscription_name and subscription_name in role_resource_name:
                matches.append(role_assignment)
            elif subscription_number and subscription_number == role_resource_name[0:4]:
                matches.append(role_assignment)
        if role_type:
            matches = list(filter(lambda role_assignment: role_type.lower() in role_assignment.roleDefinition.displayName.lower(), matches))
        if len(matches) != 1:
            print(f"Unable to determine subscription based on filters. Got {len(matches)} potential matches.")
            print([f"{match.roleDefinition.resource.displayName} ({match.roleDefinition.displayName})" for match in matches])
            print("Add an additional 'role_type' filter with '-r' to further narrow down the matches")
            exit(1)
        match = matches[0]
        print(f"Found Eligible Role Assignment matching filters: {match.roleDefinition.resource.displayName} ({match.roleDefinition.displayName})")
        return match
    except StopIteration as not_found:
        print(f"No matches were returned when filtering eligible role assignments:")
        print(f"Filter:\n\tSubscription name: {subscription_name}\n\tSubscription Number: {subscription_number}\n\tRole Type: {role_type}")
        sys.exit(1)


@click.group()
def cli():
    pass


@cli.command()
@click.option("-t", "--tenant-id", default=TENANT_ID, help="The tenant ID in which the Azure subscription exists")
@click.option("-s", "--subscription-name", help="The name of the subscription to activate")
@click.option("-n", "--subscription-number", help="The name (prefix) of the subscription to activate (e.g. 'S398')")
@click.option(
    "-r", "--role-type",
    help="Specify the role type to activate if multiple roles are found for a subscription. (e.g. 'Owner' or 'Contributor')"
)
def activate(tenant_id: str, subscription_name: str = None, subscription_number: str = None, role_type: str = None):
    try:
        if not tenant_id:
            raise ValueError("You must provide a value for 'tenant_id'.")
        if not subscription_name and not subscription_number:
            raise ValueError("You must specify either 'subscription_name' or 'subscription_number'.")
        pim_token, subject = get_pim_access_token(tenant_id)
        subject_id = subject.get("id")
        role_assignments = get_role_assignments(subject_id, token=pim_token)
        role_assignment = get_role_assignment_by_subscription(
            role_assignments,
            subscription_name=subscription_name,
            subscription_number=subscription_number,
            role_type=role_type
        )
        role_assignment_request = request_role_assignment(
            subject_id,
            role_assignment.resourceId,
            role_assignment.roleDefinitionId,
            role_assignment.id,
            token=pim_token
        )
        print(f"Role '{role_assignment.roleDefinition.resource.displayName}' is now {role_assignment_request.assignmentState}")
        print(f"\tThe role activation expires at {role_assignment_request.schedule.endDateTime}")
    except KeyboardInterrupt:
        sys.exit(1)
    except ValueError as err:
        print(err)
        sys.exit(1)


if __name__ == "__main__":
    cli()
