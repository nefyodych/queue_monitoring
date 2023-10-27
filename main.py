import yaml, glob, os, socket, time
from util import fn_log_os, express_msg, send_email
from apscheduler.schedulers.background import BlockingScheduler

print(__file__)

# Логирование, создание папки для логов
os.system(f'md logs')

fn_log_os(mess='Выполняется запуск программы', type='sys') 

# Получаем настройки программки из config.yaml
def load_config_yaml(config_path):
    # проверка наличия файла
    if not os.path.exists(config_path):
        fn_log_os(mess=f"load_config_yaml: Конфигурационный файл не найден по пути {config_path}", type='sys')
        raise ValueError(f"Конфигурационный файл не найден по пути {config_path}")
    with open(config_path, "r", encoding='utf-8') as stream:
        try:
            fn_log_os(mess=f"load_config_yaml: Конфигурационный файл {config_path} загружен!", type='sys')
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            raise

# Читаем конфиг
cfg = load_config_yaml('config.yaml')

# Получаем имя сервера
server_name = socket.gethostname()  

# Конфиг EXPRESS
try:
    express_active = cfg['express_active']
except:
    express_active = False
fn_log_os(mess=f"express_active = {express_active}", type='sys')    

# Конфиг smtp
try:
    smtp_active = cfg['smtp_active']
except:
    smtp_active = False
fn_log_os(mess=f"smtp_active = {smtp_active}", type='sys')       

# Конфиг журнала win
try:
    event_active = cfg['event_active']
except:
    event_active = False
fn_log_os(mess=f"event_active = {event_active}", type='sys') 

timer = cfg['timer']

# Конфиг BOX
try:
    config_box = cfg['CONFIG_BOX']
    list_cfg = list(config_box)
except Exception as err:
    express_msg(cfg, f'Ошибка чтения конфига - {err}')
    fn_log_os(mess=f'config_box: Ошибка чтения конфига - {err}', type='sys') 

# Таймер
def countdown(t):
    while t:
        mins, secs = divmod(t, 60)
        timer = '{:02d}:{:02d}'.format(mins, secs)
        print("Следующий запуск через:", timer, end="\r")
        time.sleep(1)
        t -= 1

# Программа мониторинга
def start_programm():

    fn_log_os(mess=f"Запущена процедура поиска очередей - start_programm", type='sys')   

    # Массив, в который записывается информация при появлении очереди в каталогах
    text_arr = []

    # Проверяем каждый объект по условию и записываем находки в text_arr в виде каталог:очередь
    for i_cfg in list_cfg:
        extract_all_data = config_box[i_cfg]
        extract_path = extract_all_data['path']

        ex_level = 'INFO'

        # Проверка доступности папки.
        check_folder = os.path.exists(extract_path)

        # Если доступна папка
        if check_folder:
            try:
                queue_warn = int(extract_all_data['queue_warn'])
                if queue_warn < 0:
                    queue_warn = 0
            except:
                queue_warn = 0

            try:
                queue_crit = int(extract_all_data['queue_crit'])
                if queue_crit < 0:
                    queue_crit = 0
            except:
                queue_crit = 0

            # Получаем длину очереди в каталоге
            chechk_len = len(glob.glob(f'{extract_path}/*'))

            # Если warn = true, crit = false
            if queue_warn and not queue_crit:
                print('warn = true, crit = false')
                if chechk_len >= queue_warn:
                    ex_level = 'WARNING'
                    create_arr = [extract_path, chechk_len, ex_level, 1]
                    text_arr.append(create_arr)
                print(f' {i_cfg}, warn = {queue_warn}, crit = {queue_crit}, len = {chechk_len}, lvl = {ex_level}')

            # Если warn = false, crit = true
            elif not queue_warn and queue_crit:
                print('warn = false, crit = true')
                if chechk_len >= queue_crit:
                    ex_level = 'CRITICAL'
                    create_arr = [extract_path, chechk_len, ex_level, 1]
                    text_arr.append(create_arr)
                print(f' {i_cfg}, warn = {queue_warn}, crit = {queue_crit}, len = {chechk_len}, lvl = {ex_level}')

            # Если warn = true, crit = true   
            elif queue_warn and queue_crit:
                print('warn = true, crit = true')
                # Если параметр задан корректно, warn < crit
                if queue_warn < queue_crit:
                    if chechk_len >= queue_warn and chechk_len <= queue_crit:
                        ex_level = 'WARNING'
                        create_arr = [extract_path, chechk_len, ex_level, 1]
                        text_arr.append(create_arr)
                    elif chechk_len >= queue_crit:
                        ex_level = 'CRITICAL'
                        create_arr = [extract_path, chechk_len, ex_level, 1]
                        text_arr.append(create_arr)
                    print(f'{i_cfg}, warn = {queue_warn}, crit = {queue_crit}, len = {chechk_len}, lvl = {ex_level}')
                # Если параметр задан некорректно warn >= crit
                elif queue_warn >= queue_crit:
                    if chechk_len >= queue_warn:
                        ex_level = 'CRITICAL'
                        create_arr = [extract_path, chechk_len, ex_level, 1]
                        text_arr.append(create_arr)
                    print(f' {i_cfg}, warn = {queue_warn}, crit = {queue_crit}, len = {chechk_len}, lvl = {ex_level}')

            elif not queue_warn and not queue_crit:
                print('warn = false, crit = false')
                print(f' {i_cfg}, warn = {queue_warn}, crit = {queue_crit}, len = {chechk_len}, lvl = {ex_level}')
        # Если папка недоступна
        else:
            print(f'Папка недоступна {extract_path}')
            ex_level = 'CRITICAL'
            create_arr = [extract_path, 0, ex_level, 0]
            text_arr.append(create_arr)



    # Блок работы с журналом windows
    if text_arr and event_active:
        # Создание события в журнале для tivoli
        for i_str in text_arr:
            if i_str[3] == 1:
                if i_str[2] == 'CRITICAL':
                    os.system(f'eventcreate /L Application /T Error /SO Mon_TKI_ESPP /ID 16 /D "Очереди на ТКИ, см лог мониторинга"')
                elif i_str[2] == 'WARNING': 
                    os.system(f'eventcreate /L Application /T Warning /SO Mon_TKI_EPS /ID 15 /D "Очереди на ТКИ, см лог мониторинга"')
            else:
                os.system(f'eventcreate /L Application /T Error /SO Mon_TKI_ESPP /ID 16 /D "Недоступна {i_str[0]}"')

    # Запись в лог
    if text_arr:
        for i_str in text_arr:
            if i_str[3] == 1:
                fn_log_os(mess=f"{i_str[2]} - {i_str[0]} = {i_str[1]}", type='mon')
            else:
                fn_log_os(mess=f"{i_str[2]} - {i_str[0]} = недоступна!!!", type='mon')  

    # Блок работы с EXPRESS
    if text_arr and express_active:
        # Составляем текст для express
        text_for_express_create = ''
        for i_str in text_arr:
            if i_str[3] == 1:
                i_str_mod = f"{i_str[2]} - ***{i_str[0]}*** = ***{i_str[1]}***"
                text_for_express_create = text_for_express_create + i_str_mod + "\n"
            else:
                i_str_mod  = f"{i_str[2]} - ***{i_str[0]}*** = ***недоступна!!!***"
                text_for_express_create = text_for_express_create + i_str_mod + "\n"

        text_for_express = f"Мониторинг очередей ГИД \n\n{text_for_express_create}"
        # Вызываем отправку
        express_msg(cfg, text_for_express)

    # Блок работы с почтой
    if text_arr and smtp_active:
        # Составляем текст для почты
        text_for_smtp_create = ''
        for i_str in text_arr:
            if i_str[3] == 1:
                i_str_mod = f"<p>{i_str[2]} - <b>{i_str[0]}</b> = <b>{i_str[1]}</b></p>"
                text_for_smtp_create = text_for_smtp_create + i_str_mod + "\n"
            else:
                i_str_mod = f"<p>{i_str[2]} - <b>{i_str[0]}</b> = <b> недоступна!!!</b></p>"
                text_for_smtp_create = text_for_smtp_create + i_str_mod + "\n"

        text_for_smtp = f"""
            <p>Мониторинг очередей ГИД</p>
            {text_for_smtp_create}
        """

        # Вызываем отправку
        send_email(cfg, 'Мониоринг очередей ГИД', text_for_smtp)

    fn_log_os(mess=f"Завершена процедура поиска очередей - start_programm", type='sys')       

def del_log():
    path_logs = './logs/'
    fn_log_os(mess=f"Запущена чистка логов - del_log", type='sys')   
    try:
        now = time.time()
        for filename in os.listdir(path_logs):
            filestamp = os.stat(os.path.join(path_logs, filename)).st_mtime
            seven_days_ago = now - 14 * 86400
            if filestamp < seven_days_ago:
                print(filename)
                os.remove(os.path.join(path_logs, filename))
        fn_log_os(mess=f"Чистка логов выполнена успешно", type='sys')          
    except:
        fn_log_os(mess=f"Ошибка в чистке логов", type='sys')  

del_log()
start_programm()

if __name__ == '__main__':
    fn_log_os(mess=f"Планировщик запущен.", type='sys')
    # Активация планировщика задач
    scheduler = BlockingScheduler()
    scheduler.add_job(start_programm, 'interval', minutes=cfg['timer'])
    scheduler.add_job(del_log, 'interval', days=1)
    try:
        scheduler.start()
    except KeyboardInterrupt:
        fn_log_os(mess=f"Ошибка в работе планировщика.", type='sys')
        pass
scheduler.shutdown()