import json
import os

class AnnotionConfigure(object):
    def __init__(self,jsonPath):
        try:
            with open(jsonPath,'r') as f:
                self.data=json.load(f)
        except Exception as e:
            print(e)

        self.classes=self.data["classes"]
        self.clsToId={}
        for i in self.classes:
            self.clsToId[i["cls"]]=i["id"]

    @classmethod
    def loadConfig(cls,*args,**kwargs):
        AnnotionConfigure._instance=AnnotionConfigure(*args,**kwargs)
    @classmethod
    def saveConfig(cls,savePath):
        pass

    @classmethod
    def instance(cls):
        if not hasattr(AnnotionConfigure,'_instance'):
            AnnotionConfigure._instance=AnnotionConfigure('./config/annotionConfig.json')
        return AnnotionConfigure._instance

    def getClassConfig(self):
        ret=[]
        for i in range(len(self.classes)):
            ret.append([self.classes[i]["id"],self.classes[i]["cls"],self.classes[i]["color"]])
        return ret
    def getClassCnt(self):
        return len(self.classes)
    def getClassColor(self,i):
        return self.classes[i]['color']

    def getKeypointConfigByClassId(self,cid):
        ret=[]
        kpoints=self.classes[cid]["keypoints"]
        for i in range(len(kpoints)):
            ret.append([kpoints[i]["id"],kpoints[i]["name"],kpoints[i]["color"]])
        return ret
    def getKeypointCntByClassId(self,cid):
        return len(self.classes[cid]["keypoints"])
    def getKeypointColor(self,cid,i):
        return self.classes[cid]['keypoints'][i]['color']

class GeneralConfigure(object):
    def __init__(self):
        self.setup()

    def setup(self):
        self.annotiondir='./annotion'
        self.outputFormat='json'
        self.fileFormat='{}_anno.json'
        self.imagedir=None
        self.index=None
        self.images=[]
        if not os.path.exists(self.annotiondir):
            os.mkdir(self.annotiondir)

    @classmethod
    def instance(cls):
        if not hasattr(GeneralConfigure,'_instance'):
            GeneralConfigure._instance=GeneralConfigure()
        return GeneralConfigure._instance

    def setAnnotionDir(self,path):
        self.annotiondir=path

    # Make sure the folder without not-image file
    def setImageDir(self,path):
        self.imagedir=path
        self.images=os.listdir(path)
        if len(self.images)>0:
            self.index=-1
        else:
            self.index=None

    def getImageName(self):
        if self.index==None:
            return None
        return self.images[self.index]
    def getImageDir(self):
        return self.imagedir
    def getAnnotionDir(self):
        return self.annotiondir
    def getAnnotionFileName(self):
        if self.index==None:
            return None
        return self.fileFormat.format(self.images[self.index].split('.')[0])

    def getNext(self):
        if self.index==None:
            return [None,None]
        if self.index<len(self.images)-1:
            self.index+=1
            image=os.path.join(self.imagedir,self.images[self.index])
            anno=os.path.join(self.annotiondir,self.fileFormat.format(self.images[self.index].split('.')[0]))
            if os.path.exists(anno):
                return [image,anno]
            else:
                return [image,None]
        else:
            return [None,None]

    def getPre(self):
        if self.index==None:
            return [None,None]
        if self.index>0:
            self.index-=1
            image=os.path.join(self.imagedir,self.images[self.index])
            anno=os.path.join(self.annotiondir,self.fileFormat.format(self.images[self.index].split('.')[0]))
            if os.path.exists(anno):
                return [image,anno]
            else:
                return [image,None]
        else:
            return [None,None]