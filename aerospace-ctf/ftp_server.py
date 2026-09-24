from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

authorizer = DummyAuthorizer()


authorizer.add_anonymous(
    "./ftp_share",
    perm="elr"
)

handler = FTPHandler
handler.authorizer = authorizer
handler.banner = "Aerospace Research FTP Server"

server = FTPServer(
    ("0.0.0.0", 2121),
    handler
)

print("[+] Aerospace FTP challenge running")
print("[+] Port: 2121")
print("[+] Anonymous access: ENABLED")

server.serve_forever()
