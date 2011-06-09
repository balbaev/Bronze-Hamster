import sys
import os
import hashlib
import cPickle
import zipfile
dir_backup="Directory"
os.system("7za x delta.7z")
os.system("7za -y x delta.zip")
os.remove("delta.7z")
os.remove("delta.zip")
remove=open("remove.txt","r")
for line in remove:
  line=line.rstrip('\n')
  os.remove(line)
remove.close()
os.remove("remove.txt")
dict={}
checksum=open(os.path.join(dir_backup,"..","chksm.txt"),'w')

for (path,dirs,files) in os.walk(dir_backup):
  if ((dirs == [] ) & (files == [])):
    os.rmdir(path)

for (path,dirs,files) in os.walk(dir_backup):
  for filename in files:
    f_temp=open(os.path.join(path,filename),'r')
    content=f_temp.read()
    m=hashlib.md5()
    m.update(content)
    dict[os.path.join(path,filename)]=m.hexdigest()
    f_temp.close()
cPickle.dump(dict,checksum)