from gigachat import GigaChat

def ask_ai(question):
    with GigaChat(credentials="MDE5YWZjOGYtMDZhYi03OTFjLTk4NGItZDVhMTY3NzA4YmY5OjVjNjUyNmQ3LWM3MzktNDg3MS05NWU2LWVkZmUwYmI2MWExOA==", verify_ssl_certs=False) as giga:
        response = giga.chat(question)
        return(response.choices[0].message.content)