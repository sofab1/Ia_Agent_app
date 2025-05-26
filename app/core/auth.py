from fastapi.security import OAuth2PasswordBearer

# Créer une instance unique de OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


