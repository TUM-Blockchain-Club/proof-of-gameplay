from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

def sign(score):
    privateKey = b'\xec\x9e\x7f-\x81t\xe6\xd0\xf5\xa1\xea\x96CS\xd8{\xf8\x95;\xc4\xc4\xe5\xf3\xc3\xc1;\xd7\xc8|\x02e\x1e'
    privateKey = Ed25519PrivateKey.from_private_bytes(privateKey)
    #msg = bytes(str(playerID)+'#'+str(score), 'utf-8')
    msg = bytes(str(score), 'utf-8') #just the score gets signed
    return privateKey.sign(msg)


if __name__ == "__main__":
    msg = sign(20)
    publicKey = b'5\xbaAg%H\xc1\x08B\x08Vi\xf9(\xe38\xcb(1\xf7Y\x8bMTeIH\xdd\xff\xb2Il'
    publicKey = Ed25519PublicKey.from_public_bytes(publicKey)
    publicKey.verify(msg, bytes(str(20), 'utf-8'))
    