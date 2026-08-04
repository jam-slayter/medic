#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скачивает официальные обложки (превью) видео с Rutube и вписывает их в index.html.

Как это работает:
  1. Находит в index.html все видео (по data-modal-embed с id ролика Rutube).
  2. Для каждого id запрашивает https://rutube.ru/api/video/{id}  → берёт поле thumbnail_url.
  3. Скачивает картинку в папку img/  (файл rutube-<id>.jpg).
  4. Подставляет её в соответствующую видео-карточку.
  5. Делает резервную копию index.html.bak.

Как запустить:
  • Положите этот файл рядом с index.html (в ту же папку) и папкой img/.
  • Нужен установленный Python 3 (обычно уже есть). Интернет обязателен.
  • В терминале в этой папке выполните:   python fetch_rutube_thumbs.py
  • Готово — обложки скачаются и пропишутся. Если что-то пойдёт не так,
    вернуть исходник можно из index.html.bak.

Зависимостей ставить не нужно — используется только стандартная библиотека.
"""
import re, os, sys, json, urllib.request

HERE   = os.path.dirname(os.path.abspath(__file__))
INDEX  = os.path.join(HERE, 'index.html')
IMGDIR = os.path.join(HERE, 'img')
WIDTH  = 800   # ширина обложки в пикселях (Rutube отдаёт нужный размер)
UA     = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36'


def http_get(url, as_json=False):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': '*/*'})
    with urllib.request.urlopen(req, timeout=25) as r:
        data = r.read()
    return json.loads(data.decode('utf-8')) if as_json else data


def main():
    if not os.path.exists(INDEX):
        print('❌ Не найден index.html рядом со скриптом. Положите скрипт в папку сайта.')
        sys.exit(1)

    html = open(INDEX, encoding='utf-8').read()

    # id ролика из data-modal-embed + текущая картинка в этой же карточке
    pattern = re.compile(
        r'data-modal-embed="https://rutube\.ru/play/embed/([0-9a-fA-F]+)/"'
        r'[\s\S]*?<div class="video-thumb"><img src="([^"]*)"'
    )
    matches = pattern.findall(html)
    if not matches:
        print('❌ В index.html не найдено видео (data-modal-embed). Нечего обновлять.')
        sys.exit(1)

    print(f'Найдено видео: {len(matches)}')
    os.makedirs(IMGDIR, exist_ok=True)
    open(INDEX + '.bak', 'w', encoding='utf-8').write(html)  # резервная копия

    ok = 0
    for vid, old_src in matches:
        try:
            info  = http_get(f'https://rutube.ru/api/video/{vid}/?format=json', as_json=True)
            thumb = info.get('thumbnail_url') or info.get('picture_url')
            if not thumb:
                print(f'  • {vid}: в ответе нет thumbnail_url — пропускаю (обложка прежняя)')
                continue
            thumb += ('&' if '?' in thumb else '?') + f'width={WIDTH}'

            rel_path = f'img/rutube-{vid}.jpg'
            with open(os.path.join(HERE, rel_path), 'wb') as f:
                f.write(http_get(thumb))

            # подменяем только src, сохраняя остальные атрибуты (alt, loading)
            html = html.replace(f'<img src="{old_src}"', f'<img src="{rel_path}"', 1)
            print(f'  • {vid}: обложка скачана → {rel_path}')
            ok += 1
        except Exception as e:
            print(f'  • {vid}: ошибка ({e}) — обложка оставлена прежней')

    open(INDEX, 'w', encoding='utf-8').write(html)
    print(f'\n✅ Готово. Обновлено обложек: {ok} из {len(matches)}.')
    print('   Исходная версия сохранена в index.html.bak')
    if ok < len(matches):
        print('   Часть роликов пропущена — у них осталась прежняя обложка.')


if __name__ == '__main__':
    main()
