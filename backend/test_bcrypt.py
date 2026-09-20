import logging
import sys
from passlib.context import CryptContext

def test():
    print("Testing bcrypt")
    try:
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hash = pwd_context.hash("password")
        print("Hash:", hash)
        valid = pwd_context.verify("password", hash)
        print("Valid:", valid)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test()
