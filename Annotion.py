class WrapKeyPoint(object):
    def __init__(self, rect, Id,bboxId):
        self.bboxId=bboxId
        self.id=Id
        self.rect = rect


class WrapBoundingBox(object):
    def __init__(self, rect,cls,kpointCnt, kpointIds=None):
        self.rect = rect
        self.kpointIds={}
        self.cls=cls
        if kpointIds == None:
            for i in range(kpointCnt):
                self.kpointIds[i]=None
        else:
            self.kpointIds = kpointIds
