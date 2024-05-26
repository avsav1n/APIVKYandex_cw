from collections import Counter
from datetime import datetime
from time import sleep
from os import mkdir
from shutil import rmtree
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import config
import requests
import json
import tqdm
import logging

class SoсialMedia:
    '''
    Класс-предок для классов, работающих с API социальных сетей  
    '''
    def backup_preparation(self, files='photos') -> list:
        '''
        Функция подготовки резервного копирования файлов из социальных сетей
        В качестве аргумента принимает объект класса требуемой сети и тип файлов для копирования
        '''
        if isinstance(self, ProfileVK):
            match files:
                case 'photos': 
                    return self.get_photos()
                case _: 
                    logging.warning(f'В настоящее время объекту ProfileVK '
                                    f'доступно только резервное копирование фотографий')

class ProfileVK(SoсialMedia):
    '''
    Класс для работы с API Вконтакте
    '''
    def __init__(self, id: str, token: str):
        self.id = id
        self.token = token
        self.surname, self.name = self._get_profile_info()
    
    def _get_profile_info(self) -> str:
        '''
        Функция запрашивающая информацию профиля, создаваемого объекта класса ProfileVK
        '''
        url = 'https://api.vk.com/method/account.getProfileInfo'
        params = {
            'access_token': self.token,
            'v': '5.199',
            'owner_id': self.id
        }
        response = requests.get(url, params=params)
        return response.json()['response']['last_name'], response.json()['response']['first_name']

    def __str__(self) -> str:
        '''
        Функция вывода информации объекта класса
        '''
        return (
            f'Информация по объекту класса ProfileVK\n'
            f'ID профиля: {self.id}\n'
            f'Фамилия: {self.surname}\n'
            f'Имя: {self.name}'
        )

    def get_photos(self, album='profile') -> list:
        '''
        Метод получения фотографий наибольшего размера из профиля VK
        Результатом возвращает список словарей формата 
        {'name': имя фотографии, 'size': размер фотографии, 'url': ссылка на фотографию}
        '''
        logging.info('Запуск процедуры подготовки файлов')
        url = 'https://api.vk.com/method/photos.get'
        downloaded_photos = []
        proportions = 'wzyrqpoxms' # Размеры фотографий, от большего к меньшему
        params = {
            'access_token': self.token,
            'v': '5.199',
            'owner_id': self.id,
            'album_id': album,
            'extended': '1'
        }
        response = requests.get(url, params=params)
        file = response.json()
        if response.status_code == 200 and file['response']['count']:
            all_photo_likes = Counter([photo['likes']['count'] for photo in file['response']['items']])
            pbar = tqdm.tqdm(file['response']['items'], ncols=100)
            for photo in pbar:
                photo_info = {}
                max_sized_photo = sorted(photo['sizes'], key=lambda x: proportions.index(x['type']))[0]
                if all_photo_likes[photo['likes']['count']] > 1:
                    date = datetime.fromtimestamp(photo['date']).date()
                    photo_name = f'{photo['likes']['count']}, {date}, id{photo['id']}.jpg'
                else: 
                    photo_name = f'{photo['likes']['count']}.jpg'
                photo_info = {
                    'name': photo_name, 
                    'size': max_sized_photo['type'], 
                    'url': max_sized_photo['url']
                }
                downloaded_photos.append(photo_info)
                pbar.set_description(f"Подготовка файла '{photo_info['name']}'")
                sleep(0.3)
            logging.info(f'Файлы подготовлены. Количество файлов - {len(downloaded_photos)}')
            return downloaded_photos
        else: 
            if file['response']['count'] == 0:
                logging.warning(f'Фотографии в альбоме {album} отсутствуют')
            else:
                logging.warning(f'Невозможно получить доступ к данным, ошибка {response.status_code}')

class ProfileYandex:
    '''
    Класс для работы с API Yandex
    '''
    def __init__(self, token: str):
        self.token = token
        self.id, self.surname, self.name = self._get_profile_info()
        self.headers = {
            'Authorization': f'OAuth {self.token}'
        }

    def _get_profile_info(self) -> str:
        '''
        Функция запрашивающая информацию профиля, создаваемого объекта класса ProfileYandex
        '''
        url = 'https://login.yandex.ru/info'
        params = {
            'oauth_token': self.token,
            'format': 'json'
        }
        response = requests.get(url, params=params)
        return response.json()['id'], response.json()['last_name'], response.json()['first_name']

    def __str__(self) -> str:
        '''
        Функция вывода информации объекта класса
        '''
        return (
            f'Информация по объекту класса ProfileYandex\n'
            f'ID профиля: {self.id}\n'
            f'Фамилия: {self.surname}\n'
            f'Имя: {self.name}'
        )

    def delete_folder(self, path):
        '''
        Метод удаления папки с Yandex Диска
        '''
        url = 'https://cloud-api.yandex.net/v1/disk/resources'
        params = {
            'path': path
        }
        requests.delete(url, params=params, headers=self.headers) 

    def create_folder(self, object) -> str:
        '''
        Метод создания папки на Yandex Диске
        '''
        url = 'https://cloud-api.yandex.net/v1/disk/resources/'
        params = {
            'path': f'Backup from id{object.id} {datetime.now().date()}'
        }
        response = requests.get(url, params=params, headers=self.headers)
        if response.status_code == 404:
            requests.put(url, params=params, headers=self.headers)
        return params['path']

    def backup(self, object, files='photos'):
        '''
        Метод резервного копирования файлов на Yandex Диск
        В качестве аргумента метод принимает объект класса социальной сети и тип файлов для копирования
        Результатом выполнения функции является копирование файлов на Yandex Диск 
        и формирование файла формата .json с перечнем загруженных файлов
        '''
        logging.info(f'Инициализация процедуры резервного копирования файлов {files} ' 
                     f'на Yandex Диск id{self.id} из {type(object).__name__} id{object.id}')
        backup_files = object.backup_preparation(files)
        if not isinstance(backup_files, list):
            logging.info(f'Журнал исполнения доступен по ссылке \\progress\\progress_log.log')
            return
        uploaded_files = []
        url = 'https://cloud-api.yandex.net/v1/disk/resources/upload/'
        folder_name = self.create_folder(object)
        logging.info('Запуск процедуры резервного копирования файлов')
        pbar = tqdm.tqdm(backup_files, ncols=100)
        for file in pbar:
            params = {
                'path': f'{folder_name}/{file['name']}'
            }
            content = requests.get(file['url'])
            response = requests.get(url, params=params, headers=self.headers) 
            if response.status_code == 409:
                pbar.set_description(f"Проверка файла '{file['name']}'")
                continue
            upload_url= response.json()['href']
            response = requests.put(upload_url, files={'file': content.content})
            if response.status_code == 201:
                del file['url']
                uploaded_files.append(file)
                pbar.set_description(f"Копирование файла '{file['name']}'")
            else:
                logging.warning(f'Процедура копирования файла {file['name']} прервана, '
                                f'ошибка {response.status_code}')
                return
        with open(r'progress\backupYandex.json', 'w', encoding='utf-8') as fw:
            json.dump(uploaded_files, fw, ensure_ascii=False, indent=2)
        if uploaded_files:
            logging.info(f'Копирование на Yandex Диск завершено.'
                         f'Количество загруженных файлов - {len(uploaded_files)}')
        else:
            logging.warning(f'Подготовленные файлы уже имеются на Yandex Диске')
        logging.info(f'Информация по скопированным файлам доступна по ссылке \\progress\\backupYandex.json')
        logging.info(f'Журнал исполнения доступен по ссылке \\progress\\progress_log.log')

class ProfileGoogle:
    '''
    Класс для работы с API Google 
    (в данном проекте взаимодействие осуществляется с помощью библиотеки PyDrive)
    '''
    def __init__(self):
        gauth = GoogleAuth()
        gauth.LocalWebserverAuth()
        self.drive = GoogleDrive(gauth)
        self.id, self.surname, self.name = self._get_profile_info()

    def _get_profile_info(self) -> str:
        '''
        Функция-костыль, запрашивающая информацию профиля, создаваемого объекта класса ProfileGoogle
        '''
        file = self.drive.CreateFile()
        file.Upload()
        id = file['owners'][0]['permissionId']
        surname, name = file['owners'][0]['displayName'].split()
        file.Delete()
        return id, surname, name

    def __str__(self) -> str:
        '''
        Функция вывода информации объекта класса
        '''
        return (
            f'Информация по объекту класса ProfileGoogle\n'
            f'ID профиля: {self.id}\n'
            f'Фамилия: {self.surname}\n'
            f'Имя: {self.name}'
        )

    def create_folder(self, object):
        '''
        Метод создания папки на Google Диске
        '''
        metadata = {
            'title': f'Backup from id{object.id} {datetime.now().date()}',
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = self.drive.CreateFile(metadata)
        folder.Upload()
        return folder['id']

    def backup(self, object, files='photos'):
        '''
        Метод резервного копирования файлов на Google Диск
        В качестве аргумента метод принимает объект класса социальной сети и тип файлов для копирования
        Результатом выполнения функции является копирование файлов на Google Диск 
        и формирование файла формата .json с перечнем загруженных файлов
        '''
        logging.info(f'Инициализация процедуры резервного копирования файлов {files} ' 
                     f'на Google Диск id{self.id} из {type(object).__name__} id{object.id}')
        backup_files = object.backup_preparation(files)
        if not isinstance(backup_files, list):
            logging.info(f'Журнал исполнения доступен по ссылке \\progress\\progress_log.log')
            return        
        uploaded_files = []
        folder_id = self.create_folder(object)        
        logging.info('Запуск процедуры резервного копирования файлов')
        pbar = tqdm.tqdm(backup_files, ncols=100)
        metadata = {
            'parents': [{'id': folder_id}]
        }
        try: mkdir('cache')
        except: pass
        for file in pbar:
            content = requests.get(file['url'])
            with open(rf'cache\{file['name']}', 'wb') as fw:
                fw.write(content.content)
            data = self.drive.CreateFile(metadata)
            data.SetContentFile(rf'cache\{file['name']}')
            data['title'] = file['name']
            data.Upload()
            del file['url']
            uploaded_files.append(file)
            pbar.set_description(f"Копирование файла '{file['name']}'")
        with open(r'progress\backupGoogle.json', 'w', encoding='utf-8') as fw:
            json.dump(uploaded_files, fw, ensure_ascii=False, indent=2)
        try: rmtree('cache')
        except: pass    
        logging.info(f'Копирование на Google Диск завершено. '
                         f'Количество загруженных файлов - {len(uploaded_files)}')
        logging.info(f'Информация по скопированным файлам доступна по ссылке \\progress\\backupGoogle.json')
        logging.info(f'Журнал исполнения доступен по ссылке \\progress\\progress_log.log')

def init_logging():
    try: mkdir('progress')
    except: pass
    log_in_file = logging.FileHandler(r'progress\progress_log.log', mode='w', encoding='utf-8')
    log_in_console = logging.StreamHandler()
    logging.basicConfig(level=logging.INFO, handlers=(log_in_console, log_in_file), 
                        format='%(asctime)s %(levelname)s %(message)s')

init_logging()
vkontakte = ProfileVK(config.id_vk, config.token_vk)
yandex = ProfileYandex(config.token_yandex)
google = ProfileGoogle()

yandex.backup(vkontakte)
google.backup(vkontakte)
