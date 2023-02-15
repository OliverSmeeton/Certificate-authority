import os
import getpass

def selection_menu(options):
    """
    Displays a selection menu and returns the user's choice.
    The options should be a list of strings.
    """
    for i, option in enumerate(options):
        print(f"{i+1}. {option}")
    choice = 0
    while choice < 1 or choice > len(options):
        try:
            choice = int(input(f"Choose an option (1-{len(options)}): "))
        except ValueError:
            pass
    return choice

def passIn(): #Gets password with 6 or more characters
    print("Show/Hide Password input?")
    passCheck = False
    selection = selection_menu(["Show","Hide"])
    while passCheck == False:
        if selection == 1:
            passwd = input("PEM Password: ")
        else:
            passwd = getpass.getpass("PEM Password: ")
        
        if len(passwd) >= 6:
            passCheck = True
        else:
            print("Password too short!")
    return passwd

def slotGen(slot, passwd): #Preconfigured steps for generating PFX for YubiKey PIV slots
    match slot:
        case 1:
            keyGen("9A", "9a", "ECCP384")
            crtIssue("9A", "9a", passwd)
            pfxOut("9A", passwd)
        case 2:
            keyGen("9C", "9c", "ECCP384")
            crtIssue("9C", "9c", passwd)
            pfxOut("9C", passwd)
        case 3:
            keyGen("9E", "9e", "RSA2048")
            crtIssue("9E", "9e", passwd)
            pfxOut("9E", passwd)

def keyGen(name, cfg, type): #Generates key and CSR
    if type == "ECCP384":
        os.system(f"openssl ecparam -genkey -name secp384r1 -out {name}/{name}.key")
    elif type == "RSA2048":
        os.system(f"openssl genrsa -out {name}/{name}.key 2048")
    
    os.system(f"openssl req -new -config {name}/{cfg}.cnf -key {name}/{name}.key -nodes -out {name}.csr")

def crtIssue(name, cfg, passwd): #Issues certificate using CSR and optional config
    if cfg == "":
        os.system(f"openssl ca -config Root-CA.cnf -in {name}.csr -out {name}/{name}.crt -extensions copy -notext -passin pass:{passwd}")
    else:
        os.system(f"openssl ca -config Root-CA.cnf -in {name}.csr -out {name}/{name}.crt -extensions v3_req -extfile {name}/{cfg}.cnf -notext -passin pass:{passwd}")
    os.system(f"rm {name}.csr")

def pfxOut(name,passwd): #Combines Key, CRT and CA CRT into PFX file
    os.system(f"openssl pkcs12 -export -out {name}/{name}.pfx -inkey {name}/{name}.key -in {name}/{name}.crt -certfile certificates/CA.pem -passout pass:{passwd}")

def customCRT(passwd): #Create Key and CRT or sign existing CSR
    print("Generate new key or use provided CSR?")
    selection = selection_menu(["New Key","Sign existing CSR"])
    name = input("Name: ")
    cfg = input("config (Empty for none): ").strip()
    if selection == 1: #Generate Key and issue CRT then export to PFX
        print("Key Type:")
        selection = selection_menu(["RSA2048","ECCP384"])
        if selection == 1:
            keyGen(name, cfg, "RSA2048")
        else:
            keyGen(name, cfg, "ECCP384")
        crtIssue(name, cfg, passwd)
        pfxOut(name,passwd)
    else: #Only issue certificate
        crtIssue(name, cfg, passwd)
    
def crtRevoke(passwd):
    print("Select certificate Serial: ")
    crts = os.listdir("certificates")
    selection = selection_menu(crts)
    os.system(f"openssl ca -revoke certificates/{crts[selection-1]} -config Root-CA.cnf -passin pass:{passwd}")

def main():
    passwd = passIn()

    quit = False

    while quit == False:
        selection = selection_menu(["Generate CA","Generate YubiKey Slot","Generate Custom Certificate","Revoke","Generate CRL","Quit"])
        match selection:
            case 1: #Gen CA
                os.system("mkdir certificates")
                os.system(f"openssl req -new -x509 -sha256 -days 3650 -config Root-CA.cnf -extensions v3_req -set_serial 1 -keyout CA.key -out certificates/CA.pem -passout pass:{passwd}")
                os.system("openssl x509 -outform der -in certificates/CA.pem -out CA.crt")
                os.system("echo 02 > serial")

            case 2: #Gen YubiKey Slot
                selection = selection_menu(["9A","9C","9E"])
                slotGen(selection, passwd)

            case 3: #Gen Custom Crt
                customCRT(passwd)

            case 4: #Revoke
                crtRevoke(passwd)
 
            case 5: #Gen CRL
                os.system(f"openssl ca -config Root-CA.cnf -keyfile CA.key -cert certificates/CA.pem -gencrl -out CRL.pem -passin pass:{passwd}")
    
            case 6: #Quit
                quit = True

main()