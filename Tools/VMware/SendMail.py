# Import smtplib for the actual sending function
import smtplib

# Import the email modules we'll need
from email.mime.text import MIMEText

# Open a plain text file for reading.  For this example, assume that
# the text file contains only ASCII characters.
# with open(textfile, 'rb') as fp:
#     # Create a text/plain message
msg = MIMEText('''
Be Ready for tomorrow's Fun Event!!''')

# me == the sender's email address
# you == the recipient's email address
msg['Subject'] = "The Secret Santa's Message"
msg['From'] = 'SecretSanta@pa.com'
msg['To'] = 'sursubramani@pa.com'

# Send the message via our own SMTP server, but don't include the
# envelope header.
s = smtplib.SMTP('smtp.pa.com')
    # server = smtplib.SMTP(server)
s.ehlo()
s.starttls()
s.sendmail('SecretSanta@pa.com', ['sursubramani@pa.com'], msg.as_string())
s.quit()