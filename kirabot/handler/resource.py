import json
import os
import zipfile
from typing import Literal

from filetype import filetype
from nonebot.adapters.onebot.v11.adapter import MessageSegment

from kirabot.utils.web import async_get_content

ROOT_PATH = os.path.join(os.path.dirname(__file__), "../../resource")


class Resource:

    def __init__(self, name: str):
        """
        资源类 为每个模块分配资源文件夹
        可通过 模块名.resource 或 服务名.resource 调用这个类
        Args:
            name: 模块名称 建立的文件夹名称将于此同名
        """
        self.name = name
        self.parent = os.path.join(ROOT_PATH, self.name)
        os.makedirs(self.parent, exist_ok=True)

    def file(self, filepath: str):
        class File:
            def __init__(self, parent, file_path):
                self.path: str = os.path.realpath(os.path.join(parent, file_path))

            @property
            def exist(self) -> bool:
                return os.path.exists(self.path)

            @property
            def cqcode(self) -> str:
                if not self.exist:
                    raise FileNotFoundError(self.path)
                ext = str(os.path.splitext(self.path)[-1]).lower()
                if ext in [".png", ".jpg", ".webm", ".gif", ".bmp", ".jpeg"]:
                    # return pic2cq(self.path)
                    return f"[CQ:image,file=file:///{os.path.realpath(self.path)}]"
                elif ext in [".mp3", ".wav", ".ogg", ".flac", ".m4a"]:
                    return f"[CQ:record,file=file:///{os.path.realpath(self.path)}]"
                elif ext in [".mkv", ".mp4", ".avi", ".wmv"]:
                    return f"[CQ:video,file=file:///{os.path.realpath(self.path)}]"
                else:
                    raise TypeError("File Type Not Supported")

            @property
            def message_segment(self) -> MessageSegment:
                if not self.exist:
                    raise FileNotFoundError(self.path)
                ext = str(os.path.splitext(self.path)[-1]).lower()
                if ext in [".png", ".jpg", ".webm", ".gif", ".bmp", ".jpeg"]:
                    # return pic2cq(self.path)
                    return MessageSegment.image(os.path.realpath(self.path))
                elif ext in [".mp3", ".wav", ".ogg", ".flac", ".m4a"]:
                    return MessageSegment.record(os.path.realpath(self.path))
                elif ext in [".mkv", ".mp4", ".avi", ".wmv"]:
                    return MessageSegment.video(os.path.realpath(self.path))
                else:
                    raise TypeError("File Type Not Supported")

            async def download(self, url, proxy: bool = True, headers: dict = None):
                content = await async_get_content(url, proxy=proxy, headers=headers)
                if not os.path.splitext(self.path)[1]:
                    extension = filetype.guess_mime(content).split('/')[1]
                    self.path += f'.{extension}'
                self.save(content)

            def save(self, content, save_type: Literal['wb', 'w', 'wa'] = "wb", overwrite=False):
                if self.exist and not overwrite:
                    raise FileExistsError("File Already Exists")
                if self.exist:
                    os.remove(self.path)
                os.makedirs(os.path.split(self.path)[0], exist_ok=True)
                with open(self.path, save_type) as fp:
                    fp.write(content)

            def remove(self):
                if self.exist:
                    os.remove(self.path)
                else:
                    raise FileNotFoundError(self.path)

            @property
            def json(self):
                ext = str(os.path.splitext(self.path)[-1]).lower()
                if ext not in [".json", ".jsonc"]:
                    raise TypeError("Not a Json File")

                class json_file:
                    def __init__(self, json_path):
                        self.path = os.path.realpath(json_path)

                    @property
                    def exist(self):
                        return os.path.exists(self.path)

                    def read(self) -> dict | list:
                        if not self.exist:
                            raise FileNotFoundError(self.path)
                        else:
                            try:
                                with open(self.path, 'r', encoding='utf-8') as fp:
                                    data = json.load(fp)
                                return data
                            except json.JSONDecodeError:
                                os.remove(self.path)
                                return {}

                    def save(self, data: dict | list):
                        with open(os.path.realpath(self.path), 'w', encoding='utf-8') as fp:
                            json.dump(data, fp, ensure_ascii=False, indent=4)

                return json_file(self.path)

            @property
            def text(self):
                class text_file:
                    def __init__(self, text_path):
                        self.path = os.path.realpath(text_path)

                    @property
                    def exist(self):
                        return os.path.exists(self.path)

                    def read(self, encoding="utf8") -> str:
                        if not self.exist:
                            raise FileNotFoundError(self.path)
                        else:
                            with open(self.path, 'r', encoding=encoding) as fp:
                                data = fp.read()
                            return data

                    def save(self, text: str, encoding="utf8"):
                        with open(os.path.realpath(self.path), 'w', encoding=encoding) as fp:
                            fp.write(text)

                return text_file(self.path)

            @property
            def zip(self):
                ext = str(os.path.splitext(self.path)[-1]).lower()
                if ext not in [".zip"]:
                    raise TypeError("Not a zip File")

                class zip_file:
                    def __init__(self, zip_path):
                        self.path = os.path.realpath(zip_path)
                        self.filename = os.path.split(zip_path)

                    @property
                    def exist(self):
                        return os.path.exists(self.path)

                    def pack(self, files: list[str]) -> zipfile.ZipFile:
                        with zipfile.ZipFile(self.path, 'w', zipfile.ZIP_STORED) as zf:
                            for file in files:
                                if file:
                                    name = os.path.split(file)[-1]
                                    zf.write(file, name)
                        return zf

                return zip_file(self.path)

        return File(self.parent, filepath)

    def dir(self, dir_path: str):
        class Dir:
            def __init__(self, parent, p):
                self.path: str = os.path.realpath(os.path.join(parent, p))

            @property
            def exist(self):
                return os.path.exists(self.path)

            def create(self):
                if not self.exist:
                    os.makedirs(self.path, exist_ok=True)

            def remove(self):
                os.rmdir(self.path)

            @property
            def list(self):
                files = []
                dirs = []
                if self.exist:
                    listdir = os.listdir(self.path)
                    for p in listdir:
                        if os.path.isdir(os.path.join(self.path, p)):
                            dirs.append(p)
                        else:
                            files.append(p)
                else:
                    self.create()
                return [dirs, files]

        return Dir(self.parent, dir_path)

    get = file
