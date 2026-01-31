from web3 import Web3
import json
import time


GANACHE_RPC = "http://127.0.0.1:8545"

PRIVATE_KEY = "0xcf6a23ee2b3d83cd6956bece00934812079ab9023762048b17ad8b1e13a4bcc4"

ACCOUNT_ADDRESS = "0x6ea8Ae4A6d66fBDaCb8f44199564cB7Dc4993FD5"


w3 = Web3(Web3.HTTPProvider(GANACHE_RPC))

def health_check():
    """Check if connected to Ganache and contract is deployed"""
    if not w3.is_connected():
        return False
    
    # Check if contract exists at address
    try:
        code = w3.eth.get_code(CONTRACT_ADDRESS)
        if len(code) <= 2:  # '0x' only means no contract
            print(f"[BLOCKCHAIN] ❌ No contract at {CONTRACT_ADDRESS}")
            return False
        return True
    except Exception as e:
        print(f"[BLOCKCHAIN] Health check failed: {e}")
        return False



CONTRACT_ABI =[
	{
		"inputs": [],
		"stateMutability": "nonpayable",
		"type": "constructor"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "index",
				"type": "uint256"
			}
		],
		"name": "getImage",
		"outputs": [
			{
				"internalType": "string",
				"name": "",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "",
				"type": "string"
			},
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			},
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "getImageCount",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "index",
				"type": "uint256"
			}
		],
		"name": "getPerceptualHash",
		"outputs": [
			{
				"internalType": "string",
				"name": "",
				"type": "string"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "owner",
		"outputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "string",
				"name": "_shaHash",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "_perceptualHash",
				"type": "string"
			},
			{
				"internalType": "address",
				"name": "_uploader",
				"type": "address"
			}
		],
		"name": "storeImageHash",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	}
]


CONTRACT_ADDRESS = "0x0567DEe31b322d95B7a7e5B59727987e446e8E0f"

try:
    contract_instance = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)
except Exception as e:
    print(f"[BLOCKCHAIN] ❌ Failed to load contract: {e}")
    contract_instance = None


def store_image_on_chain(sha_hash, perceptual_hash):
    """Store image hashes on blockchain"""
    if not health_check():
        raise Exception("Blockchain not connected or contract not deployed")
    
    try:
        nonce = w3.eth.get_transaction_count(ACCOUNT_ADDRESS)

        tx = contract_instance.functions.storeImageHash(
            sha_hash,
            perceptual_hash,
            ACCOUNT_ADDRESS
        ).build_transaction({
            "from": ACCOUNT_ADDRESS,
            "nonce": nonce,
            "gas": 3000000,
            "gasPrice": w3.eth.gas_price
        })

        signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print(f"[BLOCKCHAIN] Waiting for transaction confirmation...")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        print(f"[BLOCKCHAIN] Transaction confirmed! Hash: {tx_hash.hex()}")

        return {
            "txHash": tx_hash.hex(),
            "status": receipt.status,
            "gasUsed": receipt.gasUsed
        }
    except Exception as e:
        print(f"[BLOCKCHAIN] Failed to store on chain: {e}")
        raise


def hamming_distance(hash1: str, hash2: str) -> int:
    if not hash1 or not hash2:
        return float('inf')
    
    if len(hash1) != len(hash2):
        return float('inf')
    
    try:
        # Convert hex strings to integers
        int1 = int(hash1, 16)
        int2 = int(hash2, 16)
        
        # XOR the two hashes - bits that differ will be 1
        xor_result = int1 ^ int2
        
        # Count the number of 1 bits (differing bits)
        distance = bin(xor_result).count('1')
        
        return distance
    except ValueError:
        # If conversion fails, fall back to character comparison
        distance = 0
        for c1, c2 in zip(hash1, hash2):
            if c1 != c2:
                distance += 1
        return distance


def is_similar_to_existing(new_phash: str, similarity_threshold: int = 10) -> dict:
    if not w3.is_connected():
        raise Exception("Not connected to Ganache. Is it running on http://127.0.0.1:8545?")
    
    # Check if contract is deployed
    code = w3.eth.get_code(CONTRACT_ADDRESS)
    if len(code) <= 2:
        raise Exception(f"No contract deployed at {CONTRACT_ADDRESS}. Please deploy your contract first!")
    
    try:
        print(f"[BLOCKCHAIN] Checking similarity for phash: {new_phash}")
        print(f"[BLOCKCHAIN] Contract address: {CONTRACT_ADDRESS}")
        
        # Get total images on blockchain
        total_images = contract_instance.functions.getImageCount().call()
        print(f"[BLOCKCHAIN] Total images on chain: {total_images}")
        
        if total_images == 0:
            print("[BLOCKCHAIN] No images on chain yet - Image is unique")
            return {
                "is_duplicate": False,
                "similar_images": [],
                "min_distance": None
            }
        
        similar_images = []
        min_distance = float('inf')
        
        # Compare with all existing images
        print(f"[BLOCKCHAIN] Comparing with {total_images} existing images...")
        
        for i in range(total_images):
            try:
                stored_phash = contract_instance.functions.getPerceptualHash(i).call()
                distance = hamming_distance(new_phash, stored_phash)
                
                if distance < min_distance:
                    min_distance = distance
                
                print(f"[BLOCKCHAIN]   Image {i}: distance={distance}")
                
                if distance <= similarity_threshold:
                    # Found similar image - fetch full details
                    image_details = contract_instance.functions.getImage(i).call()
                    similar_images.append({
                        "index": i,
                        "shaHash": image_details[0],
                        "perceptualHash": image_details[1],
                        "uploader": image_details[2],
                        "timestamp": image_details[3],
                        "distance": distance
                    })
                    print(f"[BLOCKCHAIN] SIMILAR IMAGE FOUND at index {i} (distance={distance})")
                    
            except Exception as e:
                print(f"[BLOCKCHAIN] Error checking image {i}: {e}")
                continue
        
        result = {
            "is_duplicate": len(similar_images) > 0,
            "similar_images": similar_images,
            "min_distance": min_distance if min_distance != float('inf') else None
        }
        
        if result["is_duplicate"]:
            print(f"[BLOCKCHAIN] DUPLICATE DETECTED - Found {len(similar_images)} similar image(s)")
        else:
            print(f"[BLOCKCHAIN] Image is UNIQUE (min distance: {min_distance})")
        
        return result
        
    except Exception as e:
        print(f"[BLOCKCHAIN] Error in similarity check: {e}")
        import traceback
        traceback.print_exc()
        raise




def get_total_images():
    if not health_check():
        raise Exception("Blockchain not connected")
    return contract_instance.functions.getImageCount().call()


def get_image_by_index(index):
    if not health_check():
        raise Exception("Blockchain not connected")
    return contract_instance.functions.getImage(index).call()


# ---------------------------
# STARTUP CHECK
# ---------------------------
if __name__ == "__main__":
    print("\n" + "="*60)
    print("BLOCKCHAIN CONNECTION TEST")
    print("="*60)
    
    if w3.is_connected():
        print("Connected to Ganache")
        print(f"RPC: {GANACHE_RPC}")
        print(f"Account: {ACCOUNT_ADDRESS}")
        print(f"Balance: {w3.eth.get_balance(ACCOUNT_ADDRESS) / 10**18} ETH")
    else:
        print("NOT connected to Ganache")
        print("   Make sure Ganache is running on http://127.0.0.1:8545")
    
    print(f"\nContract Address: {CONTRACT_ADDRESS}")
    code = w3.eth.get_code(CONTRACT_ADDRESS)
    if len(code) > 2:
        print(f"Contract deployed (code length: {len(code)} bytes)")
        try:
            total = contract_instance.functions.getImageCount().call()
            print(f"Total images on chain: {total}")
        except:
            print("Could not read from contract")
    else:
        print("NO CONTRACT at this address!")
        print("   Deploy your contract in Remix and update CONTRACT_ADDRESS")
    
    print("="*60 + "\n")