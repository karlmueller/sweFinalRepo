import smtplib, ssl

# information on emailing sourced from :https://realpython.com/python-send-email/#option-1-setting-up-a-gmail-account-for-development


class send_mail(object):

    def __init__(self, email_sending, email_emerg, recipient, username):
        self.port = 465 #for ssl
        self.password = 'sweJKK20cap!' #DO NOT COMMIT OR SHARE THIS PASSWORD... may need a new one for project handoff...
        self.email_emerg = email_emerg
        self.email_sending = email_sending
        self.recipient = recipient
        #create ssl context:
        

        self.username = username
        self.addr = '301 Clifton CT, Cincinnati OH 45219'

        self.msg = self.construct_mail()
        self.mail_send()

    def construct_mail(self):

        msg = f'''\
            Subject: EMERGENCY: {self.username} has fallen!
            

            {self.username} needs your assistance urgently!
            Please assist at {self.addr} and alert emergency services!

            Thanks for trusting your loved ones to Swe Technologies!
            '''
        
        return msg

    def mail_send(self):
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL('smtp.gmail.com', self.port, context=context) as mail_serv:
            mail_serv.login(self.email_sending, self.password)
            mail_serv.sendmail(self.email_sending, self.email_emerg, self.msg)



if __name__ == '__main__':
    send_mail('sweappnotifier@gmail.com', 'acharykr@mail.uc.edu', 'sweNotify', 'sweUser')
