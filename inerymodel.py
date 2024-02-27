from api.cline import Cline
from api.keys import INRKey

class Client() :
    def __init__(self, url) :
        self.url = url
        self.cli = Cline(self.url)
    
    def get_action_data_entry(self, code, action) :
        abi = self.cli.get_abi(code)
        for struct in abi['abi']['structs'] :
            if struct['name'] == action :
                return struct['fields']
        
    def generate_keypair(self):
        ine_key = INRKey()
        private_key = ine_key.to_wif()
        public_key = ine_key.to_public()
        keypair = { "private_key": private_key, "public_key": public_key }
        return keypair
    
    def generate_action(self, code, action, authorization, action_data) :
        data = self.cli.abi_json_to_bin(code, action, action_data)
        action_payload = {
            "account": code,
            "name": action,
            "authorization": [{
                "actor": authorization['actor'],
                "permission": authorization['permission']
            }],
            "data" : data['binargs']
        }
        return action_payload
    
    def get_table_data(self, args):
        next_key = True
        data = []
        while next_key :
            try :
                out = self.cli.get_table(args.account, args.account, args.table, lower_bound=args.lower,upper_bound = args.upper, limit=args.limit)
                lower = out['next_key']
                if not lower : 
                    next_key = False
                for row in out['rows'] :
                    data.append(row) 
            except Exception as e :
                print("Something went wrong... ", e)
        return data
    
    def get_table_n(self, args) :
        count=0
        data = []
        while count < args.count :
            try :
                out = self.cli.get_table(args.account, args.account, args.table, lower_bound=args.lower, limit=args.count, reverse=args.reverse)
                lower = out['next_key']
                if not lower : 
                    next_key = False
                for row in out['rows'] :
                    data.append(row) 
                    count+=1
            except Exception as e :
                print("Something went wrong... ", e)
        return data
        

class Account() :
    def __init__(self, name, pkey, key) :
        self.name = name
        self.pkey = pkey
        self.key = key
        
class Contract(Account) :
    def __init__(self, abi):
        self.abi = abi
        self.tables = []
        self.actions = []

if __name__ == "__main__" : 
    c = Client("https://tas.blockchain-servers.world")
    #print(c.get_action_data_entry("inerygui", "adduser"))
    c.get_table_all()