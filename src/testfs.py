# -*- coding: utf-8 -*-
import os, stat, errno, sys
import fuse
import logging

fuse.fuse_python_api = (0, 2)

source_point = '/'

def get_real_path(path):
    return source_point + "/" + path
    
def flags2mode(flags):
    md = {os.O_RDONLY: 'r', os.O_WRONLY: 'w', os.O_RDWR: 'w+'}
    m = md[flags & (os.O_RDONLY | os.O_WRONLY | os.O_RDWR)]
    if flags & os.O_APPEND:
        m = m.replace('w', 'a', 1)
    return m+"b"

class transparentFS(fuse.Fuse):
    def __init__(self, *args, **kw):
        fuse.Fuse.__init__(self, *args, **kw)
        self.README = 'This is simple FS\n'
        self.fi = {}
        logging.basicConfig(filename='example.log',level=logging.DEBUG)

    def osopen(self,path,flags,mode=0666):
        result = os.fdopen(os.open(path,flags,mode),flags2mode(flags))
        logging.debug("osopen: flags2mode: %s, \t file_handle: %s" % (flags2mode(flags), result))
        return result
                        
    # getattr вызывается при получении информации об объекте ФС. Например, при использовании команды ls
    def getattr(self, path):
        logging.debug("getattr: %s" % path)
        path = get_real_path(path)
        return os.stat(path)
        # В объекте fuse.Stat() вернем интересующую информацию        
    
    # readdir вызывается при попытке просмотра содержимого каталога. Например, при использовании ls

    def readdir(self, path, offset):
        logging.debug("readdir: %s" % path)
        path = get_real_path(path)
        for x in ['.', '..'] + os.listdir(os.path.abspath(path)):
            yield fuse.Direntry(x)
        """# В каждом каталоге есть '.' и '..'
        yield fuse.Direntry('.')
        yield fuse.Direntry('..')
        if path == '/':
            # Кроме того, в '/' есть еще и 'README' и 'simple'
            yield fuse.Direntry('README')
            yield fuse.Direntry('simple')"""
            
    def mkdir(self, path, mode):
        path = get_real_path(path)
        return os.mkdir(path, mode)
    
    """def access(self, path, mode):
        path = get_real_path(path)
        if not os.access(path, mode):
            return -fuse.EACCES"""
        #return os.access(path, mode)
    
    def rmdir(self, path):
        path = get_real_path(path)
        return os.rmdir(path)
    
    def mknod(self, path, mode, dev):
        path = get_real_path(path)
        return os.mknod(path, mode, dev)
    
    def unlink(self, path):
        path = get_real_path(path)
        return os.unlink(path)
    
    def rename(self, pathfrom, pathto):        
        return os.rename(pathfrom, pathto)
    
    def chmod(self, path, mode):
        path = get_real_path(path)
        return os.chmod(path, mode)
    
    def chown(self, path, uid, gid):
        path = get_real_path(path)
        return os.chown(path, uid, gid)
    
    def symlink(self, src, dst):
        return os.symlink(src, dst)
    
    def truncate(self, fd, length):
        return os.ftruncate(fd, length)
    
    # open вызывается при попытки открыть файл. Мы должны проверить флаги доступа - наш единственный файл '/README' доступен только на чтение

    def open(self, path, flags):
        logging.debug("open: %s, flags: %s" % (path, flags))
        path = get_real_path(path)
        fd = os.open(path, flags)
        if fd < 0:
            return -errno.EACCES
        self.fi[path] = fd
        return 0
                
        #return self.osopen(path, flags)
    
    # read вызывается при попытки прочитать данные из файла
    # offset - смещение в читаемом файле
    # size - размер считываемого ("запрощенного") блока
    # read возвращает считанные символы
    
    def read(self, path, size, offset, fh=None):
        logging.debug("read: %s" % path)
        path = get_real_path(path)
        fd = self.fi[path]
        #os.lseek(fd, offset, 2)
        return os.read(fd, size)
        
    def write(self, path, buf, offset, fh=None):
        logging.debug("write: %s" % path)
        path = get_real_path(path)
        fd = self.fi[path]
        os.lseek(fd, offset, 2)
        return os.write(fd, buf)
    
    # statfs вызывается в ответ на запрос информации о ФС

    def statfs(self):
        # Вернем информацию в объекте класса fuse.StatVfs
        st = fuse.StatVfs()
        # Размер блока
        st.f_bsize = 1024
        st.f_frsize = 1024
        st.f_bfree = 0
        st.f_bavail = 0
        # Количество файлов
        st.f_files = 2
        # Количество блоков
        # Если f_blocks == 0, то 'df' не включит ФС в свой список - понадобится сделать 'df -a'
        st.f_blocks = 4
        st.f_ffree = 0
        st.f_favail = 0
        st.f_namelen = 255
        return st
    
def runFS(src):
    usage='transparent FS ' + fuse.Fuse.fusage
    global source_point
    source_point = src
    fs = transparentFS(version="%prog " + fuse.__version__,usage=usage,dash_s_do='setsingle')
    fs.parse(errex=1)
    fs.main()