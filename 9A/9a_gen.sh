export name="9A"
export cfg="9a"

openssl ecparam -genkey -name secp384r1 -out $name.key

openssl req -sha256 -new -config $cfg.cnf -key $name.key -nodes -out $name.csr

openssl x509 -req -in $name.csr -CA ../CA.crt -CAkey ../CA.key -CAcreateserial -out $name.crt -days 1825 -extensions v3_req -extfile $cfg.cnf

openssl pkcs12 -export -out $name.pfx -inkey $name.key -in $name.crt -certfile ../CA.crt

rm $name.csr