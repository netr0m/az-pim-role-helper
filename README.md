# Azure Privileged Identity Management Role Activator
This project eases the process of activating an Azure PIM role by allowing activation via the command line.

## Requirements
### Packages
```bash
$ pip install -r requirements.txt
```

### Variables
- The tenantId of your tenant
    - Can be specified as either an environment variable (`TENANT_ID=1234[...]`), or via the `-t / --tenant-id` option.

## Usage
The `list` command takes a single named argument:
- `-t, --tenant-id`: The tenantId of your tenant
```bash
$ python3 main.py list -t <tenant_id>
```

The `activate` command takes four arguments:
- `-t, --tenant-id`: The tenantId of your tenant
- `-s, --subscription-name`: The (partial) name of the subscription to activate. E.g. `data-tool`
- `-n, --subscription-number`: The number (prefix) of the subscription to activate. E.g. `S398`
- `-r, --role-type`: The (partial) name of the role type to activate. Only necessary if multiple eligible roles exist for a subscription. E.g. `owner` or `contrib` (contributor)
```bash
$ python3 main.py activate -t <tenant_id> [-s <subscription_partial_name>] [-n <subscription_number>] [-r <role_type>]
# e.g.
$ python3 main.py activate -t "1234-5678[...]" -n S398 -r "owner"
$ python3 main.py activate -s data-tool

$ python3 main.py activate --help
Usage: main.py activate [OPTIONS]

Options:
  -t, --tenant-id TEXT            The tenant ID in which the Azure
                                  subscription exists
  -s, --subscription-name TEXT    The name of the subscription to activate
  -n, --subscription-number TEXT  The name (prefix) of the subscription to
                                  activate (e.g. 'S398')
  -r, --role-type TEXT            Specify the role type to activate if
                                  multiple roles are found for a subscription.
                                  (e.g. 'Owner' or 'Contributor')
  --help                          Show this message and exit.

```

### Creating an alias for ease-of-use
1. Create a virtual environment in the project directory: `$ python3 -m venv .venv`
2. Activate the virtual environment: `$ source .venv/bin/activate`
3. Install the required dependencies: `$ pip install -r requirements.txt`
4. Add an alias to your shell's `.rc` file (e.g. `~/.bashrc`, `~/.zshrc`, etc.)
```bash
alias pim='<PATH_TO_PROJECT_SRC>/.venv/bin/python3 <PATH_TO_PROJECT_SRC>/main.py'
# e.g.
alias pim='~/projects/etc/az-pim-role-helper/.venv/bin/python3 ~/projects/etc/az-pim-role-helper/main.py'
```
5. Source the `.rc` file
6. Run `pim`
  - List all eligible roles: `$ pim list -t <tenant_id>`
  - Activate a role: `$ pim activate -t <tenant_id> -n S398 -r owner`