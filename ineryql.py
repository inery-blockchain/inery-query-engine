import argparse, json, os
from api.cline import Cline
from api.keys import INRKey
from inerymodel import Client, Account, Contract

import ecdsa

def generate_key_pair():
    # Create a new key pair
    sk = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
    vk = sk.get_verifying_key()

    # Encode the keys in the expected EOSIO format
    private_key = sk.to_string().hex()
    public_key = vk.to_string().hex()

    # Add EOS prefix to the public key
    public_key = "INE" + public_key

    return private_key, public_key

c = Cline("https://tas.blockchain-servers.world")

cli = Client("https://tas.blockchain-servers.world")

def end(msg):
    print(msg)
    exit()

def get_table_all(args):
    args.limit = -1
    args.lower = ""
    args.upper = ""
    out = cli.get_table_data(args)
    print(out)

def get_table_first(args):
    args.reverse = False
    args.lower = ""
    args.upper = ""
    out = cli.get_table_n(args)
    print(out)

def get_table_last(args):
    args.reverse = True
    args.lower = ""
    args.upper = ""
    out = cli.get_table_n(args)
    print(out)

def get_table_range(args):
    args.limit = -1
    out = cli.get_table_data(args)
    print(out)
    

def get_table_one(args):
    next_key = True
    data = []
    while next_key :
        try :
            out = c.get_table(args.account, args.account, args.table, lower_bound=args.row_id, upper_bound=args.row_id, limit=1)
            lower = out['next_key']
            if not lower : 
                next_key = False
            for row in out['rows'] :
                data.append(row) 
        except Exception as e :
            print("Something went wrong... ", e)
            return e
    print(data)
    return data

def get_structure(args) :
    try :
        abi = c.get_abi(args.account)
    except Exception as e :
        print(json.loads(str(e)[7:].replace("'", "\""))["error"]["details"][0]["message"])
        exit()
    print(abi)
    
def get_compositions(args) :
    compositions = []
    tables=[]
    try :
        abi = c.get_abi(args.account)
    except Exception as e :
        print(json.loads(str(e)[7:].replace("'", "\""))["error"]["details"][0]["message"])
        exit()
    tbls = abi["abi"]["tables"]
    for t in tbls :
        tables.append({"name" : t["name"], "type" : t["type"]})
    structures = abi["abi"]["structs"]
    if args.a :
        for tbl in tables :
            data = { "name" : tbl["name"] }   
            for e in structures :
                if e["name"] == tbl["type"] : 
                    data["fields"] = e["fields"]

            compositions.append(data)
        print(compositions)
    else :
        print(tables)

def get_composition(args) :
    tables =[]
    try :
        abi = c.get_abi(args.account)
    except Exception as e :
        print(json.loads(str(e)[7:].replace("'", "\""))["error"]["details"][0]["message"])
        return
    for t in abi["abi"]["tables"] :
        tables.append(t["name"])
    if args.composition not in tables :
        print("Composition not found")
        return
    for a in abi["abi"]["structs"] :
        if args.composition == a["name"] :
            composition = {"name" : a["name"], "fields" : a["fields"]}
            print(composition)
            return

def get_actions(args) :
    try :
        abi = c.get_abi(args.account)
    except Exception as e :
        print(json.loads(str(e)[7:].replace("'", "\""))["error"]["details"][0]["message"])
        exit()
    actions_a = []
    actions = []
    for a in abi["abi"]["actions"] :
        actions.append({"name" : a["name"], "type" : a["type"]})
    structures = abi["abi"]["structs"]
    if args.a :
        for act in actions :
            data = { "name" : act["name"] }   
            for e in structures :
                if e["name"] == act["name"] :
                    data["fields"] = e["fields"]

            actions_a.append(data)
        print(actions_a)
    else :
        print(actions)

def get_action(args) :
    try :
        abi = c.get_abi(args.account)
    except Exception as e :
        print(json.loads(str(e)[7:].replace("'", "\""))["error"]["details"][0]["message"])
        exit()
    for a in abi["abi"]["structs"] :
        if args.action == a["name"] :
            action = {"name" : a["name"], "fields" : a["fields"]}
            print(action)
            return
    print("Action not found")

def generate_keypair(type) : 
    keypair = cli.generate_keypair()
    print(keypair)

def create_account(args) :
    account_info = ""
    try :
        account_info = c.get_account(args.account_name)
    except Exception as e :
        error = json.loads(str(e)[7:].replace("'", "\""))["error"]["details"][0]["message"]
    if account_info :
        end("Account Name is already taken")
    newaccount_data = {
        "creator" : args.creator_name,
        "name" : args.account_name,
        "owner" : {
          "threshold" : 1,
          "keys" : [{"key" : args.owner_public_key, "weight" : 1}],
          "accounts" : [],
          "waits" : []  
        },
        "active" : {
          "threshold" : 1,
          "keys" : [{"key" : args.active_public_key, "weight" : 1}],
          "accounts" : [],
          "waits" : []  
        }
    }
    allocate_data = {
        "payer" : args.creator_name,
        "receiver" : args.account_name,
        "quant" : "1000000 BYTE"
    }
    newaccount_payload = {
    "account": "inery",
    "name": "newaccount",
    "authorization": [{
        "actor": args.creator_name,
        "permission": "active"
    }]
    }
    allocate_payload = {
    "account": "inery",
    "name": "allocate",
    "authorization": [{
        "actor": args.creator_name,
        "permission": "owner"
    }]
    }
    # Converting payload to binary
    try :
        data1 = c.abi_json_to_bin(newaccount_payload['account'], newaccount_payload['name'], newaccount_data)
        newaccount_payload['data'] = data1['binargs']

        data2 = c.abi_json_to_bin(allocate_payload['account'], allocate_payload['name'], allocate_data)
        allocate_payload['data'] = data2['binargs']
    except :
        end("Wrong data")

    # final transaction formed
    trx = {"actions": [newaccount_payload, allocate_payload]}

    # use Inery key for signing transaction
    key = INRKey(args.creator_permission)
    try:
        out = c.push_transaction(trx, key, broadcast=True)
    except :
        end("Somethings wrong...")
        
        

def main():
    parser = argparse.ArgumentParser(description='Inery Database Command-Line Tool')

    # Create subparsers for the main commands
    subparsers = parser.add_subparsers(title='commands', dest='command')

    # Create subparser for the "get" command
    get_parser = subparsers.add_parser('get', help='Retrieve data')
    
    create_parser = subparsers.add_parser('create', help='Create Various items on blockchain')

    create_items_parser = create_parser.add_subparsers(title='subcommands', dest='subcommand')
    
    # Create subparser for the "table" subcommand
    get_table_parser = get_parser.add_subparsers(title='subcommands', dest='subcommand')
    get_table_parser.required = True
    
    
    # Create subparser for the "create" command
    

    # Subcommand: all
    all_parser = get_table_parser.add_parser('all', help='Retrieve all data from a table')
    all_parser.add_argument('account', help='Account name')
    all_parser.add_argument('table', help='Table name')
    all_parser.set_defaults(func=get_table_all)

    # Subcommand: first
    first_parser = get_table_parser.add_parser('first', help='Retrieve first x rows from a table')
    first_parser.add_argument('account', help='Account name')
    first_parser.add_argument('table', help='Table name')
    first_parser.add_argument('count', type=int, help='Number of rows to retrieve')
    first_parser.set_defaults(func=get_table_first)

    # Subcommand: last
    last_parser = get_table_parser.add_parser('last', help='Retrieve last x rows from a table')
    last_parser.add_argument('account', help='Account name')
    last_parser.add_argument('table', help='Table name')
    last_parser.add_argument('count', type=int, help='Number of rows to retrieve')
    
    last_parser.set_defaults(func=get_table_last)

    # Subcommand: range
    range_parser = get_table_parser.add_parser('range', help='Retrieve rows within a range from a table')
    range_parser.add_argument('account', help='Account name')
    range_parser.add_argument('table', help='Table name')
    range_parser.add_argument('lower', type=int, help='Starting index')
    range_parser.add_argument('upper', nargs='?', help='Ending index', default='')
    
    range_parser.set_defaults(func=get_table_range)

    # Subcommand: one
    one_parser = get_table_parser.add_parser('one', help='Retrieve a single row by ID from a table')
    one_parser.add_argument('account', help='Account name')
    one_parser.add_argument('table', help='Table name')
    one_parser.add_argument('row_id', help='Row ID')
    one_parser.set_defaults(func=get_table_one)
    
    # Get Structure
    struct_parser = get_table_parser.add_parser('structure', help='Show Database structure')
    struct_parser.add_argument('account', help="Database Account Name")
    struct_parser.set_defaults(func=get_structure)

    # Get Compositions
    compositions_parser = get_table_parser.add_parser('compositions', help='Show Database structure')
    compositions_parser.add_argument('account', help="Database Account Name")
    compositions_parser.add_argument('-a', help="Show composition records", action="store_true")
    compositions_parser.set_defaults(func=get_compositions)

    # Get Composition
    actions_parser = get_table_parser.add_parser('composition', help='Show Database Composition')
    actions_parser.add_argument('account', help="Database Account Name")
    actions_parser.add_argument('composition', help="Database Composition Name")
    actions_parser.set_defaults(func=get_composition)

    # Get Actions
    actions_parser = get_table_parser.add_parser('actions', help='Show Database Actions')
    actions_parser.add_argument('account', help="Database Account Name")
    actions_parser.add_argument('-a', help="Show composition records", action="store_true")
    actions_parser.set_defaults(func=get_actions)

    # Get Action
    actions_parser = get_table_parser.add_parser('action', help='Show Database Action')
    actions_parser.add_argument('account', help="Database Account Name")
    actions_parser.add_argument('action', help="Database Action Name")
    actions_parser.set_defaults(func=get_action)
    
    # Create Account
    account_create_parser = create_items_parser.add_parser('account', help="Create account on blockchain")
    account_create_parser.add_argument('creator_name', help="Creator Account Name")
    account_create_parser.add_argument('account_name', help="New Account Name")
    account_create_parser.add_argument('owner_public_key', help="Account Owner Public Key")
    account_create_parser.add_argument('active_public_key', help="Account Active Public key")
    account_create_parser.add_argument('creator_permission', help="Private key of creator account")
    account_create_parser.set_defaults(func=create_account)

    # Create Keypair
    keypair_create_parser = create_items_parser.add_parser('keypair', help="Create Inery keypair")
    keypair_create_parser.add_argument('tyoe', nargs='?', help='Ending index', default='')
    keypair_create_parser.set_defaults(func=generate_keypair)
    

    args = parser.parse_args()

    if args.command == 'get':
        args.func(args)

    if args.command == 'create':
        args.func(args)

if __name__ == '__main__':
    main()

