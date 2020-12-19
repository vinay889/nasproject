from smb.SMBConnection import SMBConnection

userID="USER1"
password="vinay143"
client_machine_name="DESKTOP-92IOI0O"
server_name="DESKTOP-92IOI0O"
server_ip="192.168.43.178"
conn = SMBConnection(userID, password, client_machine_name, server_name, use_ntlm_v2 = True)
conn.connect(server_ip, 139)
Response = conn.listShares(timeout=30)
print(Response)


# from smb.SMBConnection import SMBConnection
# userID="tonprem2"
# password="abcd@12345678"
# client_machine_name="bkc-netapp-poc"
# # CIF Server
# server_name="nasbkc1-srv.nseroot.com"
# server_ip="172.20.200.202"
# conn = SMBConnection(userID, password, client_machine_name, server_name, use_ntlm_v2 = True, is_direct_tcp= True)
# assert conn.connect(server_ip, 445)
# print(conn)
# response = conn.listShares(timeout=30)
# print(response)
