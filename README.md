# [Курсовая работа «Резервное копирование»](https://github.com/netology-code/py-diplom-basic)
## Ход выполнения
* В качестве вспомогательного, создан класс `SoсialMedia`, осуществляющий перенаправление функцией `backup_preparation` на нужный метод принимаемого класса для подготовки данных для резервного копирования
* Создан класс `ProfileVK`, позволяющий работать с API ВКонтакте. Для создания класса необходимо ввести ID профиля и OAuth-токен
>В рамках данного проекта используется метод `get_photos`, осуществляющий подготовку фотографий из профиля
* Создан класс `ProfileYandex`, позволяющий работать с API Yandex Диска. Для создания класса необходимо ввести OAuth-токен
>В рамках данного проекта используется метод `backup`, осуществляющий копирование файлов из принимаемого профиля социальных сетей (ВКонтакте)
* Создан класс `ProfileGoogle`, позволяющий работать с API Google Диска. Работа с Google Диском осуществляется с помощью библиотеки `PyDrive`
>В рамках данного проекта используется метод `backup`, осуществляющий копирование файлов из принимаемого профиля социальных сетей (ВКонтакте)
* Для выполнения резервного копирования реализован следующий синтаксис `{в}хранилище.backup({из}соц.сеть, что копировать)`
* Отслеживание процесса выполнения программы осуществляется с помощью стандартной библиотеки `logging`. Вывод сообщений происходит как в файл, так и в консоль 
* С помощью библиотеки `tqdm` добавлена визуализация подготовки и загрузки файлов (с динамическим описанием процесса)
* Обработаны большиство исключений, которые были выявлены в процессе выполнения проекта