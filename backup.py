import sys
import os
import hashlib
import cPickle
import zipfile
dir_backup="steelstorm"
dict={}
prefix = "ionice -c2 -n7 nice -n19 "

for (path,dirs,files) in os.walk(dir_backup):
  if ((dirs == [] ) & (files == [])):
    os.rmdir(path)

try:
  checksum=open(os.path.join(dir_backup,"..","chksm.txt"),'r')
  dict=cPickle.load(checksum)
  checksum.close()
except IOError:

  checksum=open(os.path.join(dir_backup,"..","chksm.txt"),'w')
  
  for (path,dirs,files) in os.walk(dir_backup):
    for filename in files:
      f_temp=open(os.path.join(path,filename),'r')
      content=f_temp.read() #reads into memory
      m=hashlib.md5()
      m.update(content)
      dict[os.path.join(path,filename)]=m.hexdigest()
      f_temp.close()
  
  cPickle.dump(dict,checksum)
  checksum.close()
  delta=zipfile.ZipFile(os.path.join(dir_backup,"..","delta.zip"),'w')
  
  for (path,dirs,files) in os.walk(dir_backup):
    for filename in files:
      delta.write(os.path.join(path,filename))
  delta.close()
  
  os.system(prefix + "7za -mx=9 a delta.7z delta.zip")
  os.remove("delta.zip")
  
  remove=open(os.path.join(dir_backup,"..","remove.txt"),'w')
  remove.close()
  exit()

remove=open(os.path.join(dir_backup,"..","remove.txt"),'w')
for key in dict.keys():
  if(os.path.exists(key) != 1):
    remove.write(key)
    remove.write('\n')
    del dict[key]
remove.close()

delta=zipfile.ZipFile(os.path.join(dir_backup,"..","delta.zip"),'w')
for (path,dirs,files) in os.walk(dir_backup):
  for filename in files:
    f_temp=open(os.path.join(path,filename),'r')
    content=f_temp.read()
    m=hashlib.md5()
    m.update(content)
    f_temp.close()
    try:
      if(dict[os.path.join(path,filename)] != m.hexdigest()):
	delta.write(os.path.join(path,filename))
	dict[os.path.join(path,filename)] = m.hexdigest()
    except KeyError:
      delta.write(os.path.join(path,filename))
      dict[os.path.join(path,filename)] = m.hexdigest()
f=open(os.path.join(dir_backup,"..","chksm.txt"),'w')
cPickle.dump(dict,f)
f.close()
delta.close()
os.system(prefix + "7za -mx=9 a delta.7z delta.zip")
os.remove("delta.zip")