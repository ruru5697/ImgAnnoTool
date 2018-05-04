import matplotlib
from matplotlib.widgets import Cursor

matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from PIL import Image
import matplotlib.patches as patches
from PyQt5.QtWidgets import QMessageBox
from enum import Enum
from Annotion import *
from configure import *
import json


class CanvasStatus(Enum):
    NONE = 0
    CREATE_BBOX = 1
    SELECT_BBOX = 2
    SELECT_KPOINT = 3
    MOVE_BBOX = 4
    MOVE_KPOINT = 5
    MOTIFY_BBOX_LU = 6
    MOTIFY_BBOX_RU = 7
    MOTIFY_BBOX_LD = 8
    MOTIFY_BBOX_RD = 9
    CREATE_KPOINT = 10


class Canvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = plt.Figure()
        FigureCanvas.__init__(self, self.fig)
        self.parent = parent
        self.subfig = self.fig.add_subplot(111)
        self.cursor = Cursor(self.subfig, useblit=False, color='gray', linewidth=1)
        self.cursor.visible = False
        self.subfig.figure.canvas.mpl_connect('button_press_event', self.on_button_press_event)
        self.subfig.figure.canvas.mpl_connect("button_release_event", self.on_button_release_event)
        self.subfig.figure.canvas.mpl_connect('motion_notify_event', self.on_motion_notify_event)
        # self.subfig.figure.canvas.mpl_connect('axes_enter_event', self.on_axes_enter_event)
        self.subfig.figure.canvas.mpl_connect('pick_event', self.on_pick_event)

        self.status = CanvasStatus.NONE
        self.pickerCnt = 0
        self.bboxs = {}
        self.kpoint = {}
        self.selectPicker = None
        self.clickPointDist = None
        self.rectrdpoint = None
        self.prange = 0.1
        self.keypointCnt = 0
        self.nextbegin = 0
        self.image=None

    def updateCanvas(self, path):
        self.subfig.cla()
        self.image = Image.open(path)
        self.subfig.imshow(self.image)
        self.cursor = Cursor(self.subfig, useblit=False, color='gray', linewidth=1)
        self.cursor.visible = False
        self.draw()
        self.status = None
        self.selectPicker = None
        self.clickPointDist = None
        self.rectrdpoint = None
        self.pickerCnt = 0
        self.bboxs = {}
        self.kpoint = {}
        self.keypointCnt = 0
        self.nextbegin = 0
        maxsize = max(self.image.width, self.image.height)
        self.prange = maxsize / 100

    def on_button_press_event(self, ev):
        if ev.button == 1:
            if self.status == CanvasStatus.CREATE_BBOX:
                self.bboxs[self.pickerCnt].rect.set_xy([ev.xdata, ev.ydata])
                self.subfig.add_patch(self.bboxs[self.pickerCnt].rect)
                self.selectPicker = self.pickerCnt
                self.pickerCnt += 1
            elif self.status == CanvasStatus.SELECT_BBOX:
                if self.selectPicker == None:
                    self.status = CanvasStatus.NONE
                    return
                if not self.checkInBBox(ev.xdata, ev.ydata, self.selectPicker):
                    self.status = CanvasStatus.NONE
                    self.bboxs[self.selectPicker].rect.set_alpha(1.0)
                    self.bboxs[self.selectPicker].rect.set_hatch(None)
                    self.selectPicker = None
                    print('cancel select bbox')
                else:
                    self.status = self.checkHowMotifyBBox(ev.xdata, ev.ydata, self.selectPicker, self.prange)
                    self.clickPointDist = [ev.xdata - self.bboxs[self.selectPicker].rect.get_x(),
                                           ev.ydata - self.bboxs[self.selectPicker].rect.get_y()]
                    self.rectrdpoint = [
                        self.bboxs[self.selectPicker].rect.get_x() + self.bboxs[self.selectPicker].rect.get_width(),
                        self.bboxs[self.selectPicker].rect.get_y() + self.bboxs[self.selectPicker].rect.get_height()]
                    if self.status != CanvasStatus.MOVE_BBOX:
                        self.cursor.visible = True
                        self.draw()
            elif self.status == CanvasStatus.SELECT_KPOINT:
                self.kpoint[self.selectPicker].rect.set_alpha(1.0)
                self.bboxs[self.kpoint[self.selectPicker].bboxId].rect.set_alpha(1.0)
                self.status = None
        if ev.button == 3:
            if self.status == CanvasStatus.SELECT_BBOX:
                if self.checkInBBox(ev.xdata, ev.ydata, self.selectPicker):
                    # self.nextbegin=(i+1)%AnnotionConfigure.instance().getKeypointCntByClassId(
                    #    self.bboxs[self.selectPicker].cls
                    # )
                    self.nextbegin = self.nextKeypointIndex(self.bboxs[self.selectPicker], self.nextbegin)
                    if self.nextbegin == None:
                        print("bounding box for '{}' have enough key point".format(
                            AnnotionConfigure.instance().getClassConfig()[self.bboxs[self.selectPicker].cls][1]))
                        return
                    self.bboxs[self.selectPicker].kpointIds[self.nextbegin] = self.pickerCnt
                    self.kpoint[self.pickerCnt] = WrapKeyPoint(
                        patches.Rectangle([ev.xdata - self.prange / 2, ev.ydata - self.prange / 2], self.prange,
                                          self.prange,
                                          picker=self.pickerCnt,
                                          edgecolor=None,
                                          facecolor=AnnotionConfigure.instance().getKeypointColor(
                                              self.bboxs[self.selectPicker].cls, self.nextbegin
                                          ),
                                          ),
                        self.nextbegin,
                        self.selectPicker
                    )
                    self.parent.addKeypoint(self.nextbegin,self.bboxs[self.selectPicker].cls,self.selectPicker,self.pickerCnt)
                    self.subfig.add_patch(self.kpoint[self.pickerCnt].rect)
                    self.pickerCnt += 1
                    self.status = CanvasStatus.CREATE_KPOINT
                    print('create keypoint')
            elif self.status == CanvasStatus.SELECT_KPOINT:
                self.status = CanvasStatus.MOVE_KPOINT
        self.draw()

    def on_motion_notify_event(self, ev):
        if ev.xdata==None or ev.ydata==None:
            return
        if self.status == CanvasStatus.CREATE_BBOX:
            self.cursor.onmove(ev)
            if ev.button == 1:
                self.bboxs[self.selectPicker].rect.set_width(min(self.image.width,max(0,ev.xdata)) - self.bboxs[self.selectPicker].rect.get_x())
                self.bboxs[self.selectPicker].rect.set_height(min(self.image.height,max(0,ev.ydata)) - self.bboxs[self.selectPicker].rect.get_y())
        elif self.status == CanvasStatus.MOVE_BBOX:
            self.bboxs[self.selectPicker].rect.set_x(min(self.image.width,max(0,ev.xdata)) - self.clickPointDist[0])
            self.bboxs[self.selectPicker].rect.set_y(min(self.image.height,max(0,ev.ydata)) - self.clickPointDist[1])
            self.draw()
        elif self.status == CanvasStatus.MOTIFY_BBOX_RU:
            self.bboxs[self.selectPicker].rect.set_y(min(self.image.height,max(0,ev.ydata)))
            self.bboxs[self.selectPicker].rect.set_width(min(self.image.width,max(0,ev.xdata)) - self.bboxs[self.selectPicker].rect.get_x())
            self.bboxs[self.selectPicker].rect.set_height(self.rectrdpoint[1] - min(self.image.height,max(0,ev.ydata)))
        elif self.status == CanvasStatus.MOTIFY_BBOX_RD:
            self.bboxs[self.selectPicker].rect.set_width(min(self.image.width,max(0,ev.xdata)) - self.bboxs[self.selectPicker].rect.get_x())
            self.bboxs[self.selectPicker].rect.set_height(min(self.image.height,max(0,ev.ydata)) - self.bboxs[self.selectPicker].rect.get_y())

        elif self.status == CanvasStatus.MOTIFY_BBOX_LU:
            self.bboxs[self.selectPicker].rect.set_x(min(self.image.width,max(0,ev.xdata)))
            self.bboxs[self.selectPicker].rect.set_y(min(self.image.height,max(0,ev.ydata)))
            self.bboxs[self.selectPicker].rect.set_width(
                self.rectrdpoint[0] - self.bboxs[self.selectPicker].rect.get_x())
            self.bboxs[self.selectPicker].rect.set_height(
                self.rectrdpoint[1] - self.bboxs[self.selectPicker].rect.get_y())
        elif self.status == CanvasStatus.MOTIFY_BBOX_LD:
            self.bboxs[self.selectPicker].rect.set_x(min(self.image.width,max(0,ev.xdata)))
            self.bboxs[self.selectPicker].rect.set_height(min(self.image.height,max(0,ev.ydata)) - self.bboxs[self.selectPicker].rect.get_y())
            self.bboxs[self.selectPicker].rect.set_width(self.rectrdpoint[0] - min(self.image.width,max(0,ev.xdata)))
        elif self.status == CanvasStatus.MOVE_KPOINT:
            self.kpoint[self.selectPicker].rect.set_xy(
                [min(self.image.width,max(0,ev.xdata)) - self.prange / 2,
                 min(self.image.height,max(0,ev.ydata)) - self.prange / 2]
            )
            self.draw()

    def on_button_release_event(self, ev):
        if ev.button == 1:
            if self.status == CanvasStatus.CREATE_BBOX:
                self.status = CanvasStatus.NONE
                if self.bboxs[self.selectPicker].rect.get_height() == 0. or self.bboxs[
                    self.selectPicker].rect.get_width == 0:
                    self.subfig.patches.remove(self.bboxs[self.selectPicker].rect)
                    self.bboxs[self.selectPicker] = None
                    self.pickerCnt -= 1
                else:
                    self.repairBBox()
                    self.parent.addBBox(self.bboxs[self.selectPicker].cls,self.selectPicker)
                self.selectPicker = None
                self.cursor.visible = False
            elif self.status == CanvasStatus.MOTIFY_BBOX_RD or self.status == CanvasStatus.MOTIFY_BBOX_LU or \
                            self.status == CanvasStatus.MOTIFY_BBOX_LD or self.status == CanvasStatus.MOTIFY_BBOX_RU:
                self.status = CanvasStatus.SELECT_BBOX
                self.repairBBox()
                self.cursor.visible = False
                self.clickPoint = None
            elif self.status == CanvasStatus.MOVE_BBOX:
                self.status = CanvasStatus.SELECT_BBOX
                self.clickPoint = None
        elif ev.button == 3:
            if self.status == CanvasStatus.CREATE_KPOINT:
                self.parent.setFocusOnPredefineKeypointListview(
                    self.nextKeypointIndex(self.bboxs[self.selectPicker], self.nextbegin))
                self.status = CanvasStatus.SELECT_BBOX
            elif self.status == CanvasStatus.MOVE_KPOINT:
                self.status = CanvasStatus.SELECT_KPOINT

        self.draw()

    def on_pick_event(self, ev):
        if ev.mouseevent.button == 1 and self.status != CanvasStatus.CREATE_BBOX:
            if self.status == CanvasStatus.SELECT_BBOX:
                return
            if self.status == CanvasStatus.SELECT_KPOINT:
                self.kpoint[self.selectPicker].rect.set_alpha(1.0)
                self.bboxs[self.kpoint[self.selectPicker].bboxId].rect.set_alpha(1.0)
            self.selectPicker = ev.artist._picker
            self.status = CanvasStatus.SELECT_BBOX
            self.nextbegin = 0
            self.parent.refreshPredefineKeypointListView(self.bboxs[self.selectPicker].cls)
            self.nextbegin = self.parent.getPredefineKeypointCurrentItem()
            if self.nextbegin == -1:
                self.nextbegin = 0
            self.parent.setFocusOnPredefineKeypointListview(
                self.nextKeypointIndex(self.bboxs[self.selectPicker], self.nextbegin)
            )
            self.parent.refreshAnnotionViewList(self.bboxs[self.selectPicker])
            self.bboxs[self.selectPicker].rect.set_alpha(0.5)
            print('select bbox')
        elif ev.mouseevent.button == 3:
            if ev.artist._picker not in self.kpoint.keys():
                return
            if self.status == CanvasStatus.SELECT_KPOINT:
                self.kpoint[self.selectPicker].rect.set_alpha(1.0)
                self.bboxs[self.kpoint[self.selectPicker].bboxId].rect.set_alpha(1.0)
            elif self.status == CanvasStatus.SELECT_BBOX:
                if self.kpoint[ev.artist._picker].bboxId != self.selectPicker:
                    self.bboxs[self.selectPicker].rect.set_alpha(1.0)
            self.selectPicker = ev.artist._picker
            self.status = CanvasStatus.SELECT_KPOINT
            self.kpoint[self.selectPicker].rect.set_alpha(0.5)
            self.bboxs[self.kpoint[ev.artist._picker].bboxId].rect.set_alpha(0.5)
            self.parent.refreshAnnotionViewList(self.bboxs[self.kpoint[self.selectPicker].bboxId],
                                                self.kpoint[self.selectPicker])
            print('select kpoint')

        self.draw()

    def create_bbox(self, cls, keypointCnt):
        if self.status == CanvasStatus.SELECT_BBOX:
            self.bboxs[self.selectPicker].rect.set_alpha(1.0)
        elif self.status == CanvasStatus.SELECT_KPOINT:
            self.kpoint[self.selectPicker].rect.set_alpha(1.0)
        self.bboxs[self.pickerCnt] = WrapBoundingBox(
            patches.Rectangle([0., 0.], 0., 0., linewidth=5, edgecolor=AnnotionConfigure.instance().getClassColor(cls),
                              facecolor='none',
                              picker=self.pickerCnt),
            cls,
            keypointCnt
        )
        self.status = CanvasStatus.CREATE_BBOX
        self.keypointCnt = keypointCnt
        self.cursor.visible = True

    def cancel_create_bbox(self):
        self.status = CanvasStatus.NONE
        self.new_bbox = None
        self.cursor.visible = False
        self.draw()

    def delete_patch(self):
        if self.selectPicker == None:
            QMessageBox.warning(self.parent, 'Error', 'Not Select object!')
            return
        if self.status == CanvasStatus.SELECT_KPOINT:
            self.subfig.patches.remove(self.kpoint[self.selectPicker].rect)
            self.parent.deleteKeypoint(self.kpoint[self.selectPicker].id,
                                       self.bboxs[self.kpoint[self.selectPicker].bboxId].cls,
                                       self.kpoint[self.selectPicker].bboxId,self.selectPicker)
            self.bboxs[self.kpoint[self.selectPicker].bboxId].kpointIds[self.kpoint[self.selectPicker].id] = None
            self.kpoint.pop(self.selectPicker)
        elif self.status == CanvasStatus.SELECT_BBOX:
            for keypointId in self.bboxs[self.selectPicker].kpointIds.keys():
                if self.bboxs[self.selectPicker].kpointIds[keypointId]==None:
                    continue
                self.subfig.patches.remove(self.kpoint[self.bboxs[self.selectPicker].kpointIds[keypointId]].rect)
                self.kpoint.pop(self.bboxs[self.selectPicker].kpointIds[keypointId])
            self.subfig.patches.remove(self.bboxs[self.selectPicker].rect)
            self.parent.deleteBBox(self.bboxs[self.selectPicker].cls,self.selectPicker)
            self.bboxs.pop(self.selectPicker)
        self.status = CanvasStatus.NONE
        self.selectPicker = None
        self.parent.setFocusOnPredefineClassListView()
        self.draw()

    def checkInBBox(self, x, y, pickerId):
        xmin = self.bboxs[pickerId].rect.get_x()
        xmax = self.bboxs[pickerId].rect.get_x() + self.bboxs[pickerId].rect.get_width()
        ymin = self.bboxs[pickerId].rect.get_y()
        ymax = self.bboxs[pickerId].rect.get_y() + self.bboxs[pickerId].rect.get_height()
        if xmin <= x and xmax >= x and ymin <= y and ymax >= y:
            return True
        else:
            return False

    def checkHowMotifyBBox(self, x, y, pickerId, prange):
        xmin = self.bboxs[pickerId].rect.get_x() + prange
        xmax = self.bboxs[pickerId].rect.get_x() + self.bboxs[pickerId].rect.get_width() - prange
        ymin = self.bboxs[pickerId].rect.get_y() + prange
        ymax = self.bboxs[pickerId].rect.get_y() + self.bboxs[pickerId].rect.get_height() - prange
        if x < xmin and y < ymin:
            return CanvasStatus.MOTIFY_BBOX_LU
        elif x < xmin and y > ymax:
            return CanvasStatus.MOTIFY_BBOX_LD
        elif x > xmax and y > ymax:
            return CanvasStatus.MOTIFY_BBOX_RD
        elif x > xmax and y < ymin:
            return CanvasStatus.MOTIFY_BBOX_RU
        else:
            return CanvasStatus.MOVE_BBOX

    def repairBBox(self):
        if self.bboxs[self.selectPicker].rect.get_width() < 0:
            self.bboxs[self.selectPicker].rect.set_x(
                self.bboxs[self.selectPicker].rect.get_x() + self.bboxs[self.selectPicker].rect.get_width()
            )
            self.bboxs[self.selectPicker].rect.set_width(
                -self.bboxs[self.selectPicker].rect.get_width()
            )
        if self.bboxs[self.selectPicker].rect.get_height() < 0:
            self.bboxs[self.selectPicker].rect.set_y(
                self.bboxs[self.selectPicker].rect.get_y() + self.bboxs[self.selectPicker].rect.get_height()
            )
            self.bboxs[self.selectPicker].rect.set_height(
                -self.bboxs[self.selectPicker].rect.get_height()
            )

    def nextKeypointIndex(self, bbox, begin):
        if begin == None:
            return None
        for i in range(begin, len(bbox.kpointIds)):
            if bbox.kpointIds[i] == None:
                return i
        if begin != 0:
            for i in range(begin):
                if bbox.kpointIds[i] == None:
                    return i
        return None

    def findNextKeypointIndex(self, begin):
        if self.status != CanvasStatus.SELECT_BBOX:
            return None
        self.nextbegin = self.nextKeypointIndex(self.bboxs[self.selectPicker], begin)
        return self.nextbegin

    def selectItem(self,pickerId,type='bbox'):
        '''

        :param pickerId: patch id
        :param type:  bbox or kpoint
        :return:
        '''
        cls=0
        if type=='bbox':
            self.status=CanvasStatus.SELECT_BBOX
            self.selectPicker=pickerId
            self.bboxs[self.selectPicker].rect.set_alpha(0.5)
            cls=self.bboxs[self.selectPicker].cls
            # update predefine_keypoint list and its index
            self.parent.refreshPredefineKeypointListView(cls)
            self.nextbegin=self.findNextKeypointIndex(0)
            self.parent.setFocusOnPredefineKeypointListview(
                self.nextKeypointIndex(self.bboxs[self.selectPicker], 0))
        elif type=='kpoint':
            self.status=CanvasStatus.SELECT_KPOINT
            self.selectPicker=pickerId
            self.kpoint[self.selectPicker].rect.set_alpha(0.5)
            self.bboxs[self.kpoint[self.selectPicker].bboxId].rect.set_alpha(0.5)
            cls=self.bboxs[self.kpoint[self.selectPicker].bboxId].cls
            self.nextbegin=self.nextKeypointIndex(self.bboxs[self.kpoint[self.selectPicker].bboxId],self.kpoint[self.selectPicker].id)
            self.parent.refreshPredefineKeypointListView(cls)
            # update predefine_keypoint list and its index
            self.parent.setFocusOnPredefineKeypointListview(
                self.nextKeypointIndex(self.bboxs[self.kpoint[self.selectPicker].bboxId], self.nextbegin))
        self.draw()

    def selectBBox(self,picker):
        if self.status==CanvasStatus.SELECT_KPOINT:
            self.kpoint[self.selectPicker].rect.set_alpha(1.0)
            self.bboxs[self.kpoint[self.selectPicker].bboxId].rect.set_alpha(1.0)
        elif self.status==CanvasStatus.SELECT_BBOX:
            self.bboxs[self.selectPicker].rect.set_alpha(1.0)
        self.selectItem(picker,'bbox')
    def selectKpoint(self,picker):
        if self.status==CanvasStatus.SELECT_KPOINT:
            self.kpoint[self.selectPicker].rect.set_alpha(1.0)
            self.bboxs[self.kpoint[self.selectPicker].bboxId].rect.set_alpha(1.0)
        elif self.status==CanvasStatus.SELECT_BBOX:
            self.bboxs[self.selectPicker].rect.set_alpha(1.0)
        self.selectItem(picker,'kpoint')

    def saveAnnotion(self):
        try:
        #for i in range(1):
            width=self.image.width
            height=self.image.height
            imagename=GeneralConfigure.instance().getImageName()
            imagedir=GeneralConfigure.instance().getImageDir()
            if imagename==None:
                return False

            boundingboxs=[]
            for bkey in self.bboxs.keys():
                cls=AnnotionConfigure.instance().getClassConfig()[self.bboxs[bkey].cls][1]
                bbox=[
                    int(self.bboxs[bkey].rect.get_x()),
                    int(self.bboxs[bkey].rect.get_y()),
                    int(self.bboxs[bkey].rect.get_x())+int(self.bboxs[bkey].rect.get_width()),
                        int(self.bboxs[bkey].rect.get_y())+int(self.bboxs[bkey].rect.get_height()),
                ]
                keypoints=[]
                for kkey in range(len(self.bboxs[bkey].kpointIds)):
                    pickerId=self.bboxs[bkey].kpointIds[kkey]
                    if pickerId!=None:
                        keypoints.append([
                            kkey,
                            int(self.kpoint[pickerId].rect.get_x())+int(self.kpoint[pickerId].rect.get_width()/2),
                                int(self.kpoint[pickerId].rect.get_y())+int(self.kpoint[pickerId].rect.get_height()/2),
                            1
                        ])
                    else:
                        keypoints.append([
                            kkey,
                            0,
                            0,
                            0
                        ])
                boundingboxs.append([{
                    'class':cls,
                    'rectangle':bbox,
                    'keypoints':keypoints
                }])
            obj=[{
                'image':{'imgName':imagename,
                'imgPath':imagedir,
                'width':width,
                'height':height},
                'bboxs':boundingboxs
            }]
            s=json.dumps(obj)
            with open(os.path.join(GeneralConfigure.instance().getAnnotionDir(),
                                   GeneralConfigure.instance().getAnnotionFileName()),'w') as f:
                f.write(s)

        except Exception as e:
            print(e)
            return False
        return True

    def loadAnnotion(self,annofile):
        with open(annofile,'r') as f:
            obj=json.load(f)[0]
        self.prange=max(obj['image']['width'],obj['image']['height'])/100
        for bbox in obj['bboxs']:
            bbox=bbox[0]
            bboxId=self.pickerCnt
            cls=bbox['class']
            clsId=int(AnnotionConfigure.instance().clsToId[cls])
            rect=bbox['rectangle']
            bboxrect=patches.Rectangle([rect[0],rect[1]],rect[2]-rect[0],rect[3]-rect[1],linewidth=5,
                                       edgecolor=AnnotionConfigure.instance().getClassColor(clsId),
                                       facecolor='none',picker=self.pickerCnt)
            self.parent.addBBox(clsId,self.pickerCnt)
            self.subfig.add_patch(bboxrect)
            self.pickerCnt+=1
            keypoints={}
            for kid,kx,ky,visible in bbox['keypoints']:
                if visible==0:
                    keypoints[kid]=None
                else:
                    keypoints[kid]=self.pickerCnt
                    kprect=patches.Rectangle([kx-self.prange/2,ky-self.prange/2],self.prange,self.prange,
                              picker=self.pickerCnt,
                              edgecolor=None,
                              facecolor=AnnotionConfigure.instance().getKeypointColor(clsId,kid))
                    self.subfig.add_patch(kprect)
                    self.kpoint[self.pickerCnt]=WrapKeyPoint(
                        kprect,kid,bboxId
                    )
                    self.parent.addKeypoint(kid,clsId,bboxId,self.pickerCnt)
                    self.pickerCnt+=1

            self.bboxs[bboxId] = WrapBoundingBox(
                bboxrect,
                clsId,
                None,
                keypoints
            )
            self.draw()