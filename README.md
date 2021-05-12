# Военная кафедра
 ## Установка зависимостей pip
 ```
 pip install -r requirements.txt
 ```
 ## Запуск
 ```
 python api/server.py --config api/config.txt
 ```

## Использование
Может стримить картинки и видео в VLC media player. Для этого:
- в VLC нажать `New stream`
- вставить ссылку вида `http://192.168.1.x:8800/screen/screen_number` \
Здесь x -- окончание айпишника (посмотреть весь ip в линукс можно по команде ```ip address``` -- нужно выбрать тот, который начинается на `192.168.1`), `screen_number` -- число от 1 до 6