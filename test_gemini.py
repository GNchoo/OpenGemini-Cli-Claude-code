import pexpect
import sys

child = pexpect.spawn('gemini chat', encoding='utf-8', timeout=5)
try:
    child.expect(pexpect.TIMEOUT, timeout=2) # Let it spit out the prompt
except pexpect.TIMEOUT:
    print("Initial output:", child.before)
    child.sendline("hello")
    try:
        child.expect(pexpect.TIMEOUT, timeout=3)
    except pexpect.TIMEOUT:
        print("Response:", child.before)
