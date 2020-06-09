import hashlib

from Crypto.PublicKey import RSA


class RSAFingerprintManager(object):
    def to_string(self, string):
        return ":".join(a + b for a, b in zip(string[::2], string[1::2]))

    def get_rsa_key(self, key_location, passphrase):
        with open(key_location) as f:
            key = RSA.importKey(f.read(), passphrase=passphrase)
        return key

    def get_private(self, key_location, passphrase=None):
        k = self.get_rsa_key(key_location, passphrase)
        sha1digest = hashlib.sha1(k.exportKey("DER", pkcs=8)).hexdigest()
        fingerprint = self.to_string(sha1digest)
        return fingerprint

    def get_public(self, key_location, passphrase=None):
        privkey = self.get_rsa_key(key_location, passphrase)
        pubkey = privkey.publickey()
        md5digest = hashlib.md5(pubkey.exportKey("DER")).hexdigest()
        fingerprint = self.to_string(md5digest)
        return fingerprint

    def extract_private_to_public(self, key_location, passphrase=None):
        # ssh-keygen -f ~/.ssh/test-dl.pem -y > ~/.ssh/test-dl.pem.pub
        privkey = self.get_rsa_key(key_location, passphrase)
        public_key = privkey.publickey().exportKey('PEM')
        return public_key.decode("ascii")
