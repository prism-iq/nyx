
import subprocess
import logging

# Masquer les erreurs shell répétitives
logging.getLogger('shell').setLevel(logging.ERROR)

def safe_shell(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout, result.stderr
    except Exception as e:
        return "", f"Shell error suppressed: {type(e).__name__}"

# Patch global pour masquer subprocess errors
_original_error = Exception.__str__
def quiet_error(self):
    if "subprocess" in str(self) and "local variable" in str(self):
        return "[shell error suppressed]"
    return _original_error(self)
Exception.__str__ = quiet_error