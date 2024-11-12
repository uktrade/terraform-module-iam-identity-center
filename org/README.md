# Organisation Data module
This module reads the organisation OU structure and accounts, and produces a map to be used in the `group` module.

For example, an org OU structure like this...
```
Root
┣━ account-a
┣━ account-b
┣━ account-c (suspended)
┣━ account-d (suspended)
┣━ OU-1
┃  ┣━ account-e
┃  ┣━ account-f
┃  ┗━ OU-2
┃     ┣━ account-g
┃     ┗━ account-h
┗━ OU-3
   ┣━ account-i
   ┗━ account-j
```
...would result in the following output. Note that `OU-2` is a child of `OU-1` in this example, so the `child_accounts` and `descendant_accounts` reasuts differ for `OU-1`  (and for `Root`) which has a deeper child structure.  

The module outputs a single object `org_ou_account_map` which contains 'child' and 'descendant' values:
```JSON
{
    "org_ou_account_map": {
        "child_accounts": {
            "Root": {
                "active": [
                    "account-a",
                    "account-b"
                ],
                "inactive": [
                    "account-c",
                    "account-d"
                ]
            },
            "OU-1": {
                "active": [
                    "account-e",
                    "account-f"
                ],
                "inactive": []
            },
            "OU-2": {
                "active": [
                    "account-g",
                    "account-h"
                ],
                "inactive": []
            },
            "OU-3": {
                "active": [
                    "account-i",
                    "account-j"
                ],
                "inactive": []
            }

        },
        "descendant_accounts": {
            "OU-1": {
                "active": [
                    "account-e",
                    "account-f",
                    "account-g",
                    "account-h"
                ],
                "inactive": []
            },
            "OU-2": {
                "active": [
                    "account-g",
                    "account-h"
                ],
                "inactive": []
            },
            "OU-3": {
                "active": [
                    "account-i",
                    "account-j"
                ],
                "inactive": []
            },
            "Root": {
                "active": [
                    "account-a",
                    "account-b",
                    "account-e",
                    "account-f",
                    "account-g",
                    "account-h",
                    "account-i",
                    "account-j"
                ],
                "inactive": [
                    "account-c",
                    "account-d"
                ]
            }
        }
    }
}
```
