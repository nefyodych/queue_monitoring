import requests, hmac, hashlib, smtplib
from datetime import datetime, date

# Функция отправки в ЕКС-МОС
def express_msg(cfg, mes):

    express_url_server = cfg['express_url_server']
    express_id_chat = cfg['express_id_chat']
    express_id_bot = cfg['express_id_bot']
    express_key_bot = cfg['express_key_bot']

    try:
        f = hmac.new(express_key_bot.encode('utf-8'),express_id_bot.encode('utf-8'),digestmod=hashlib.sha256).hexdigest()
        f = f.upper()
        r = requests.get(f"{express_url_server}/api/v2/botx/bots/{express_id_bot}/token?signature={f}",timeout=None)

        data = r.json()
        token = data["result"]

        dataString = {
            "group_chat_id": express_id_chat,
            "notification": {
            "status": "ok",
            "body": mes,
            "opts": {"silent_response": "true"},
            "bubble": [],
            "keyboard": [],
            "mentions": []
            },
            "opts": {
            "stealth_mode": "false",
            "notification_opts": {
                "send": "true",
                "force_dnd": "false"
            }
            }
        }
        url = f"{express_url_server}/api/v4/botx/notifications/direct"

        headers = {
            'Authorization': 'Bearer ' + token,
            'Content-Type':'application/json'
        }
        print('Отправляю сообщение в ЕКС-МОС:')
        print(mes)

        requests.post(url,json=dataString, headers=headers)
        print('Выполнена отправка в ЕКС-МОС')
        return True

    except:
        print('Не удалось выполнить отправку в ЕКС-МОС')
        return False     
    

# Функция взаимодействия с почтовым сервисом
def send_email(cfg, subject_smtp='Мониоринг очередей ГИД', text_smtp='Пусто'):

    smtp_user = cfg['smtp_user']
    smtp_passwd = cfg['smtp_passwd']
    smtp_server = cfg['smtp_server']
    smtp_port = '25'
    smtp_emails_list = cfg['smtp_emails_list']

    smtp_emails_list_pars = smtp_emails_list.split(', ')

    charset = 'Content-Type: text/html; charset=utf-8'
    mime = 'MIME-Version: 1.0'

    # Формируем тело письма
    body = "\r\n".join((f"From: {smtp_user}", f"To: {smtp_emails_list}", f"Subject: {subject_smtp}", mime, charset, "", text_smtp))

    try:
        print('Подключаемся к почтовому сервису')
        smtp = smtplib.SMTP(smtp_server, smtp_port)
        smtp.starttls()
        smtp.ehlo()
        print('Логинимся на почтовом сервере')
        smtp.login(smtp_user, smtp_passwd)
        print('Отправляем письмо в почту:')
        print(text_smtp)
        smtp.sendmail(smtp_user, smtp_emails_list_pars, body.encode('utf-8'))
        print('Отправка письма в почту выполнена')
        return True
    except:
        print('Что - то пошло не так...')
        return False
    finally:
        smtp.quit()


# Логирование
def fn_log_os(mess='Введите сообщение', type='sample'):
    try:
        # Получаем текущую дату и время
        current_time = datetime.now().strftime("%H:%M:%S")
        current_date = date.today()

        # Составляем имя файла
        log_name=f'log_{str(type)}_{current_date}.log'
        # Производим запись лога
        log_file = open(f'./logs/{log_name}','a')
        log_file.write(f'{current_time}: {mess}')
        log_file.write('\n')
        log_file.close()
        return True
    except:
        print('Ошибка в логировании')
        return False        