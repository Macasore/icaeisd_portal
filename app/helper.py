import random
import string

def generatePassword():
    length = random.randint(8,15)
    characters = string.ascii_letters + string.punctuation + string.digits
    password = ''.join(random.choice(characters) for i in range(length))
    return password

def sendDetailsToEmail(username, password):
    return username, password
    
    