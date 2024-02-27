from api.keys import INRKey

def generate_inery_base58_key():
    ine_key = INRKey()
    private_key = ine_key.to_wif()
    public_key = ine_key.to_public()
    return { "private_key":private_key, "public_key": public_key }

key_pair = generate_inery_base58_key()
print(key_pair)