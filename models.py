from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel

from const import DEFAULT_DURATION_MINUTES, DEFAULT_REASON


class ResourceType(str, Enum):
    AZURE_RESOURCES = "azureResources"


class PIMRequest(BaseModel):
    resource_type: ResourceType = ResourceType.AZURE_RESOURCES
    path: str
    token: str
    method: str = "GET"
    headers: Optional[dict] = {}
    params: Optional[dict] = None
    data: Optional[dict] = None
    payload: Optional[dict] = None


class RoleAssignmentSubject(BaseModel):
    id: str
    type: str
    displayName: str
    principalName: str
    email: str


class RoleResource(BaseModel):
    id: str
    type: str
    displayName: str
    status: str


class RoleDefinition(BaseModel):
    id: str
    resourceId: str
    displayName: str
    type: str
    resource: RoleResource


class RoleAssignment(BaseModel):
    id: str
    resourceId: str
    roleDefinitionId: str
    subjectId: str
    assignmentState: str
    status: str
    subject: RoleAssignmentSubject
    roleDefinition: RoleDefinition


class RoleAssignmentsResponse(BaseModel):
    value: List[RoleAssignment]


class RoleAssignmentSchedule(BaseModel):
    type: str = "Once"
    startDateTime: str = None
    endDateTime: str = None
    duration: str = f"PT{DEFAULT_DURATION_MINUTES}M"


class RoleAssignmentRequest(BaseModel):
    roleDefinitionId: str
    resourceId: str
    subjectId: str
    assignmentState: str = "Active"
    type: str = "UserAdd"
    reason: str = DEFAULT_REASON
    ticketNumber: str = ""
    ticketSystem: str = ""
    schedule: RoleAssignmentSchedule = RoleAssignmentSchedule().dict()
    linkedEligibleRoleAssignmentId: str
    scopedResourceId: str = ""


class RoleAssignmentRequestStatus(BaseModel):
    status: str
    subStatus: str
    statusDetails: List[Dict[str, str]]


class RoleAssignmentRequestResponse(BaseModel):
    id: str
    resourceId: str
    roleDefinitionId: str
    subjectId: str
    scopedResourceId: str
    linkedEligibleRoleAssignmentId: str
    type: str
    assignmentState: str
    requestedDateTime: str
    roleAssignmentStartDateTime: str
    roleAssignmentEndDateTime: str
    reason: Optional[str]
    ticketNumber: Optional[str]
    ticketSystem: Optional[str]
    condition: Optional[str]
    conditionVersion: Optional[str]
    conditionDescription: Optional[str]
    status: Optional[RoleAssignmentRequestStatus]
    schedule: RoleAssignmentSchedule
    metadata: Optional[dict]
