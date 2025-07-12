# These packages were curl-ed directly from Microsoft using

```bash
curl -O https://download.microsoft.com/download/fae28b9a-d880-42fd-9b98-d779f0fdd77f/msodbcsql18_18.5.1.1-1_amd64.apk && \
curl -O https://download.microsoft.com/download/7/6/d/76de322a-d860-4894-9945-f0cc5d6a45f8/mssql-tools18_18.4.1.1-1_amd64.apk
```

## The packages can be verified using
(Optional) Verify signature, if 'gpg' is missing install it using 'apk add gnupg':

```bash
curl -O https://download.microsoft.com/download/fae28b9a-d880-42fd-9b98-d779f0fdd77f/msodbcsql18_18.5.1.1-1_amd64.sig
curl -O https://download.microsoft.com/download/7/6/d/76de322a-d860-4894-9945-f0cc5d6a45f8/mssql-tools18_18.4.1.1-1_amd64.sig
curl https://packages.microsoft.com/keys/microsoft.asc  | gpg --import -
gpg --verify msodbcsql18_18.5.1.1-1_amd64.sig msodbcsql18_18.5.1.1-1_amd64.apk
gpg --verify mssql-tools18_18.4.1.1-1_amd64.sig mssql-tools18_18.4.1.1-1_amd64.apk
```