# Friendexing

## How to integrate with FamilySearch

1. Generate a Fernet key
```python
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key)
```
2. Use the key to encrypt your credentials
```python
fernet = Fernet(key)
print(fernet.encrypt(b'username'))
print(fernet.encrypt(b'password'))
```
3. Create a `.env` file at the top level with the following variables set to
the values printed above:
```dotenv
FERNET_KEY=
FAMILY_SEARCH_USERNAME=
FAMILY_SEARCH_PASSWORD=
```
4. Docker compose will automatically pick up the `.env` file and pass the
variables to the application, which will decrypt them and make requests to the
FamilySearch APIs for the given credentials.