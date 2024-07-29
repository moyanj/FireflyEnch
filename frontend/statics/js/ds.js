function gen_key(route, sk) {
    let salt = String(Math.floor(Date.now() / 1000));
    let data = salt + route + salt;
    data += sk;
    let encoder = new TextEncoder();
    
    let hashed = CryptoJS.SHA256(data).toString();
    
    let encoded_t = btoa(encoder.encode(salt));

    return hashed + '.' + encoded_t;
}

function verify(key, route, sk) {
    let [o_hashed, t] = key.split('.');
    let salt = atob(t);

    let data = salt + route + salt;
    data += sk;

    let hashed = CryptoJS.SHA256(data).toString();
    
    return hashed === o_hashed;
}