import boto3


def get_ram_arn(database: str, table: str | None = None) -> list[str]:
    """Return RAM resource share ARNs associated with a Lake Formation resource."""
    client = boto3.client("lakeformation")
    if table and table.upper() == "ALL_TABLES":
        resource = {"Table": {"DatabaseName": database, "TableWildcard": {}}}
    elif table:
        resource = {"Table": {"DatabaseName": database, "Name": table}}
    else:
        resource = {"Database": {"Name": database}}

    resource_shares: set[str] = set()
    next_token = None
    while True:
        request = {"Resource": resource}
        if next_token:
            request["NextToken"] = next_token

        page = client.list_permissions(**request)
        for permission in page.get("PrincipalResourcePermissions", []):
            resource_shares.update(
                permission.get("AdditionalDetails", {}).get("ResourceShare", [])
            )

        next_token = page.get("NextToken")
        if not next_token:
            break

    return sorted(resource_shares)


def get_ram_detail(ram_arn: str) -> dict[str, dict[str, str]]:
    """Return shared-principal statuses keyed by AWS account ID."""
    client = boto3.client("ram")
    principals: dict[str, dict[str, str]] = {}
    next_token = None

    while True:
        request = {
            "resourceShareArns": [ram_arn],
            "associationType": "PRINCIPAL",
        }
        if next_token:
            request["nextToken"] = next_token

        page = client.get_resource_share_associations(**request)
        for association in page.get("resourceShareAssociations", []):
            if "associatedEntity" in association:
                principal = association["associatedEntity"]
                account_id = principal.split(":")[4] if principal.startswith("arn:") else principal
                principals[account_id] = {
                    "associationType": association.get("associationType", ""),
                    "status": association.get("status", ""),
                }

        next_token = page.get("nextToken")
        if not next_token:
            break

    return dict(sorted(principals.items()))


class Test:
    
    def __init__(self):
        pass
    
    
    def needs_reprocess(self, account_id: str, ram_detail: dict) -> bool:
        if account_id not in ram_detail:
            return True
        if ram_detail[account_id].get("status") not in ["ASSOCIATED"]:
            return True
        return False
        
    def grant(self, payload: dict) -> None:
        #validar resource share sem principal
        account_id = "668848431209"
        ram = get_ram_arn(database="db_source_producer_sor", table="ALL_TABLES")
        
        ram_detail = get_ram_detail(ram[0]) if ram else {}
        needs_reprocess = self.needs_reprocess(account_id, ram_detail)
        if needs_reprocess:
            print(f"Account ID {account_id} needs reprocessing.")
        
        
        
                
    def execute(self, payload: dict) -> None:
        
        access_types = {
            "grant": self.grant
        }
        
        if "action" in payload and payload["action"] in access_types:
            access_types[payload["action"]](payload)
        
        

if __name__ == "__main__":
    test = Test()
    test.execute({"action": "grant", "key": "value"})
