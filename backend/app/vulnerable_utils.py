import hashlib
import random
import string
import os
import subprocess

def weak_hash_password(password: str) -> str:
    """
    VULNERABILITY: Use MD5 for password hashing (Weak Cryptography).
    """
    return hashlib.md5(password.encode()).hexdigest()

def generate_weak_token() -> str:
    """
    VULNERABILITY: Predictable token generation (Weak Randomness).
    """
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))

def unsafe_ping(ip: str):
    """
    VULNERABILITY: Command Injection.
    """
    # This is dangerous! Intentionally allowing injection.
    # In a real app this would be check_output or similar, but for learning we use os.system to be obvious?
    # subprocess.run is better for capturing output to show the user.
    command = f"ping -c 1 {ip}"
    try:
        result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        return result.decode()
    except subprocess.CalledProcessError as e:
        return e.output.decode()

def render_template_string_unsafe(template_str: str, context: dict):
    """
    VULNERABILITY: Server Side Template Injection (SSTI).
    """
    from jinja2 import Environment
    env = Environment()
    template = env.from_string(template_str)
    return template.render(**context)
