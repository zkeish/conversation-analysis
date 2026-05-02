from datetime import datetime, timezone
import shutil
import os
from pathlib import Path

class Utils:

    @staticmethod
    def cp(source: str, dest: str, recurse: bool=False) -> None:
        source_path = Path(source).expanduser().resolve()

        if not source_path.exists():
            raise FileNotFoundError(source_path)
        if recurse and not source_path.is_dir():
            raise ValueError("Source must be a directory when recurse=True")
        if not recurse and not source_path.is_file():
            raise ValueError("Source must be a file when recurse=False")
            
        if recurse:
            for root, dirs, files in os.walk(source):
                rel_path = os.path.relpath(root, source)
                target_dir = os.path.join(dest, rel_path)
                os.makedirs(target_dir, exist_ok=True)
                for file in files:
                    shutil.copy2(os.path.join(root, file), os.path.join(target_dir, file))
        else:
            shutil.copy2(source, dest)
        
    @staticmethod
    def mkdirs(dir) -> None:
        os.makedirs(dir)

    @staticmethod
    def ls(dir: str, recurse: bool=False) -> list[str]:
        dir_path = Path(dir).expanduser().resolve()

        if not dir_path.exists():
            raise FileNotFoundError(dir)
        if not dir_path.is_dir():
            raise ValueError("Must be a directory")
            
        if recurse:
            fnl_file_lst = list()
            for root, dirs, files in os.walk(dir):
                for f in files:
                    fnl_file_lst.append(os.path.join(root, f))
            return fnl_file_lst
        else:
            return [f for f in os.listdir(dir)]

    @staticmethod
    def mv(source: str, dest: str, recurse: bool=False) -> None:
        source_path = Path(source).expanduser().resolve()

        if source_path.exists():
            raise FileNotFoundError(source)
        if recurse and not source_path.is_dir():
            raise ValueError("Source must be a directory when recurse=True")
        if not recurse and not source_path.is_file():
            raise ValueError("Source must be a file when recurse=False")
        
        if recurse:
            for root, dirs, files in os.walk(source):
                rel_path = os.path.relpath(root, source)
                target_dir = os.path.join(dest, rel_path)
                os.makedirs(target_dir, exist_ok=True)
                for file in files:
                    shutil.move(os.path.join(root, file), os.path.join(target_dir, file))
        else:
            shutil.move(source, dest)

    @staticmethod
    def rm(dir: str, recurse: bool=False) -> None:
        dir_path = Path(dir).expanduser().resolve()

        if dir_path.exists():
            raise FileNotFoundError(dir)
        if recurse and not dir_path.is_dir():
            raise ValueError("Path must be a directory when recurse=True")
        if not recurse and not dir_path.is_file():
            raise ValueError("Path must be a file when recurse=False")
        
        if recurse:
            shutil.rmtree(dir)
        else:
            os.remove(dir)

    @staticmethod
    def format_file_datetime(prefix: str, elt_timestamp: datetime, ext: str):
        """
        Formats the current date and time using the etl_timestamp input into a specific file name format and returns the formatted file name.
        """
        now = elt_timestamp
        year = now.strftime('%Y')
        month = now.strftime('%m')
        day = now.strftime('%d')
        hour = now.strftime('%H')
        minute = now.strftime('%M')
        second = now.strftime('%S')
        file_name = f'{prefix}_{year}_{month}_{day}_{hour}_{minute}_{second}.{ext}'
        return file_name

    @staticmethod
    def format_file_now(prefix: str, ext: str):
        """
        Formats the current date and time into a specific file name format and returns the formatted file name.
        """
        now = datetime.now()
        year = now.strftime('%Y')
        month = now.strftime('%m')
        day = now.strftime('%d')
        hour = now.strftime('%H')
        minute = now.strftime('%M')
        second = now.strftime('%S')
        file_name = f'{prefix}_{year}_{month}_{day}_{hour}_{minute}_{second}.{ext}'
        return file_name