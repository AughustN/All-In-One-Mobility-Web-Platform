import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import binascii

def decrypt_busmap_data(encrypted_hex, key):
    """Decrypt BusMap API responses using AES"""
    try:
        # Convert hex string to bytes
        encrypted_data = binascii.unhexlify(encrypted_hex)
        
        # Extract IV (first 16 bytes) and ciphertext
        iv = encrypted_data[:16]
        ciphertext = encrypted_data[16:]
        
        # Create AES cipher
        cipher = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv)
        
        # Decrypt and unpad
        decrypted = unpad(cipher.decrypt(ciphertext), AES.block_size)
        
        # Parse JSON
        return json.loads(decrypted.decode('utf-8'))
    except Exception as e:
        print(f"Decryption error: {e}")
        return None

# Load the captured API responses
with open("api_responses.json", "r", encoding="utf-8") as f:
    api_responses = json.load(f)

# Get the decryption key
decryption_key = api_responses[0]["data"]
print(f"🔑 Decryption Key: {decryption_key}\n")

# Decrypt all encrypted responses
decrypted_data = []

for item in api_responses:
    if isinstance(item.get("data"), str) and len(item.get("data", "")) > 100:
        # This is likely an encrypted response
        print(f"🔓 Decrypting: {item['url']}")
        decrypted = decrypt_busmap_data(item["data"], decryption_key)
        
        if decrypted:
            decrypted_data.append({
                "url": item["url"],
                "data": decrypted
            })
            print(f"   ✅ Success! Got {len(str(decrypted))} characters of data\n")
    else:
        # Already decrypted (like the key itself or store data)
        decrypted_data.append(item)

# Save decrypted data
with open("busmap_decrypted_data.json", "w", encoding="utf-8") as f:
    json.dump(decrypted_data, f, ensure_ascii=False, indent=2)

print(f"✅ Saved {len(decrypted_data)} decrypted responses to busmap_decrypted_data.json")

# Look for the route list specifically
for item in decrypted_data:
    if "route/list" in item.get("url", ""):
        print(f"\n🚍 Found route list with {len(item['data'])} items")
        # Print first route as example
        if item['data']:
            print(f"Example route: {json.dumps(item['data'][0], indent=2, ensure_ascii=False)}")